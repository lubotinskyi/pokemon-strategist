"""Узлы графа Pokémon Team Strategist.

Каждый узел — функция, которая получает TeamState и возвращает
только те поля, которые изменила. LangGraph сам сольёт их.
"""

from src.pokeapi_tool import fetch_pokemon
from src.state import TeamState
from src.type_chart import team_weakness_summary, weaknesses_of


# ─────────────────────────────────────────────────────────────
# 1. parse — проверить вход
# ─────────────────────────────────────────────────────────────

def parse_node(state: TeamState) -> dict:
    """Очистить вход и проверить, что команда и противник не пусты."""
    selected = [s.strip().lower() for s in state.get("selected", []) if s.strip()]
    opponent = [o.strip().lower() for o in state.get("opponent", []) if o.strip()]

    if not selected:
        return {"error": "Не выбрано ни одного покемона."}
    if not opponent:
        return {"error": "Не указан противник."}
    if len(selected) > 6:
        return {"error": "В команде не может быть больше 6 покемонов."}

    return {
        "selected": selected,
        "opponent": opponent,
        "attempts": 0,
        "max_attempts": 3,
        "error": None,
    }


# ─────────────────────────────────────────────────────────────
# 2. fetch — получить данные из PokéAPI
# ─────────────────────────────────────────────────────────────

def fetch_node(state: TeamState) -> dict:
    """Запросить у PokéAPI данные всех покемонов команды и противника."""
    if state.get("error"):
        return {}

    names = state["selected"] + state["opponent"]
    data: dict = {}
    sources: list[str] = []

    for name in names:
        result = fetch_pokemon(name)
        if "error" in result:
            return {"error": result["error"]}
        data[name] = result
        sources.append(result["source"])

    return {"pokemon_data": data, "sources": sources}


# ─────────────────────────────────────────────────────────────
# 3. analyze — найти слабости команды
# ─────────────────────────────────────────────────────────────

def analyze_node(state: TeamState) -> dict:
    """Посчитать, какие типы опасны для команды."""
    if state.get("error"):
        return {}

    team_types = [
        state["pokemon_data"][name]["types"] for name in state["selected"]
    ]
    summary = team_weakness_summary(team_types)

    # Сортируем: самые опасные типы — первыми
    sorted_weak = sorted(summary.items(), key=lambda x: -x[1])

    lines = ["Слабости команды:"]
    if sorted_weak:
        for attack_type, count in sorted_weak:
            lines.append(f"- {attack_type}: уязвимы {count} покемонов")
    else:
        lines.append("- Серьёзных слабостей не найдено")

    return {"weaknesses": dict(sorted_weak), "analysis": "\n".join(lines)}


# ─────────────────────────────────────────────────────────────
# 4. propose — предложить замену
# ─────────────────────────────────────────────────────────────

def propose_node(state: TeamState) -> dict:
    """Предложить, кого убрать из команды и на кого заменить.

    Простая эвристика: убираем покемона с наибольшим числом слабостей.
    Кандидата на замену формулируем словами — позже сюда можно
    встроить LLM или список покемонов из API.
    """
    if state.get("error"):
        return {}

    team = state["selected"]

    # Найти самого «слабого» покемона
    worst_name = None
    worst_count = -1
    for name in team:
        types = state["pokemon_data"][name]["types"]
        count = len(weaknesses_of(types))
        if count > worst_count:
            worst_count = count
            worst_name = name

    # Главная слабость команды — тип, который бьёт больше всех
    main_weakness = next(iter(state["weaknesses"]), None)

    return {
        "proposed": {
            "out": worst_name,
            "in": f"покемон, устойчивый к типу {main_weakness}" if main_weakness
                  else "покемон с другим набором типов",
            "reason": f"У {worst_name} слабостей: {worst_count}",
        }
    }


# ─────────────────────────────────────────────────────────────
# 5. critic — проверить, стало ли лучше
# ─────────────────────────────────────────────────────────────

def critic_node(state: TeamState) -> dict:
    """Оценить предложенную замену.

    Если замены нет или она не улучшает команду — сообщаем об этом.
    Здесь простая проверка: если предложение сформулировано, считаем
    его валидным и увеличиваем счётчик попыток.
    """
    if state.get("error"):
        return {"improved": False}

    proposed = state.get("proposed")
    if not proposed or not proposed.get("in"):
        return {"improved": False}

    # Простая эвристика: если главная слабость была и предложена замена —
    # считаем, что стало лучше. Более честная проверка появится позже.
    improved = bool(state.get("weaknesses"))

    return {
        "improved": improved,
        "attempts": state.get("attempts", 0) + 1,
    }


# ─────────────────────────────────────────────────────────────
# 6. final — собрать итоговый ответ
# ─────────────────────────────────────────────────────────────

def final_node(state: TeamState) -> dict:
    """Сформировать итоговый текст с источниками."""
    if state.get("error"):
        return {"final_team": [], "analysis": state["error"]}

    team = state["selected"]
    lines = ["## Итоговая команда", ""]

    for name in team:
        info = state["pokemon_data"][name]
        types = ", ".join(info["types"])
        lines.append(f"- {name} ({types})")

    proposed = state.get("proposed")
    if proposed:
        lines += [
            "",
            "## Предложенная замена",
            f"- Убрать: {proposed['out']}",
            f"- Добавить: {proposed['in']}",
            f"- Причина: {proposed['reason']}",
        ]

    lines += ["", "## Источники"]
    for src in state.get("sources", []):
        lines.append(f"- {src}")

    return {"final_team": team}