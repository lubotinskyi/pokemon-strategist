"""Инструмент получения данных о покемоне из PokéAPI.

Использует только стандартную библиотеку — без сторонних HTTP-клиентов.
"""

import json
import urllib.error
import urllib.request

BASE_URL = "https://pokeapi.co/api/v2/pokemon"


def fetch_pokemon(name: str) -> dict:
    """Получить данные покемона из PokéAPI."""
    cleaned = name.strip().lower()
    if not cleaned:
        return {"error": "Пустое имя покемона."}

    url = f"{BASE_URL}/{cleaned}"

    # PokéAPI иногда отклоняет запросы без User-Agent (403).
    # Добавляем свой заголовок, чтобы сервер видел обычного клиента.
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "pokemon-strategist/1.0 (educational project)"},
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"error": f"Покемон '{cleaned}' не найден в PokéAPI."}
        return {"error": f"PokéAPI вернул ошибку {exc.code}."}
    except urllib.error.URLError:
        return {"error": "Не удалось связаться с PokéAPI. Проверьте интернет."}
    except TimeoutError:
        return {"error": "PokéAPI не ответил за 10 секунд."}
    except json.JSONDecodeError:
        return {"error": "PokéAPI вернул некорректный JSON."}

    return {
        "name": data["name"],
        "types": [t["type"]["name"] for t in data["types"]],
        "stats": {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
        "abilities": [a["ability"]["name"] for a in data["abilities"]],
        "source": url,
    }