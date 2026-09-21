"""Точка входа Pokémon Team Strategist.

Запускает граф на примере команды и печатает результат.
"""

import uuid

from src.graph import graph


def run(selected: list[str], opponent: list[str], thread_id: str | None = None) -> dict:
    """Запустить граф и вернуть итоговый State."""
    config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}

    result = graph.invoke(
        {
            "selected": selected,
            "opponent": opponent,
            "attempts": 0,
            "max_attempts": 3,
        },
        config,
    )
    return result


def main() -> None:
    """Демонстрационный запуск."""
    selected = ["pikachu", "charizard", "blastoise", "venusaur", "snorlax"]
    opponent = ["mewtwo"]

    result = run(selected, opponent)

    print("=" * 60)
    print("ИТОГИ АНАЛИЗА КОМАНДЫ")
    print("=" * 60)
    print()

    if result.get("error"):
        print(f"Ошибка: {result['error']}")
        return

    print(result["analysis"])
    print()

    if result.get("proposed"):
        p = result["proposed"]
        print("## Предложенная замена")
        print(f"- Убрать: {p['out']}")
        print(f"- Добавить: {p['in']}")
        print(f"- Причина: {p['reason']}")
        print()

    print(f"Попыток: {result.get('attempts', 0)} из {result.get('max_attempts', 3)}")
    print()

    print("## Источники")
    for src in result.get("sources", []):
        print(f"- {src}")


if __name__ == "__main__":
    main()