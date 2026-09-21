"""Таблица эффективности типов Pokémon.

Здесь только данные: какой атакующий тип бьёт какие защищающиеся типы сильно.
Используется для анализа слабостей команды.
"""

# Атакующий тип -> список типов, которым он наносит двойной урон
STRONG_AGAINST: dict[str, list[str]] = {
    "normal":   [],
    "fighting": ["normal", "rock", "ice", "dark", "steel"],
    "flying":   ["fighting", "bug", "grass"],
    "poison":   ["grass", "fairy"],
    "ground":   ["poison", "rock", "fire", "electric", "steel"],
    "rock":     ["flying", "bug", "fire", "ice"],
    "bug":      ["grass", "psychic", "dark"],
    "ghost":    ["ghost", "psychic"],
    "steel":    ["ice", "rock", "fairy"],
    "fire":     ["bug", "grass", "ice", "steel"],
    "water":    ["ground", "rock", "fire"],
    "grass":    ["ground", "rock", "water"],
    "electric": ["flying", "water"],
    "psychic":  ["fighting", "poison"],
    "ice":      ["flying", "ground", "grass", "dragon"],
    "dragon":   ["dragon"],
    "dark":     ["ghost", "psychic"],
    "fairy":    ["fighting", "dragon", "dark"],
}


def weaknesses_of(types: list[str]) -> dict[str, int]:
    """Вернуть типы, которые бьют покемона сильно, и множитель урона.

    Если у покемона два типа и оба уязвимы к одному атакующему —
    множитель становится 4 (2 × 2).
    """
    result: dict[str, int] = {}
    for attack_type, defended_types in STRONG_AGAINST.items():
        hits = sum(1 for t in types if t in defended_types)
        if hits > 0:
            result[attack_type] = 2 ** hits
    return result


def team_weakness_summary(team_types: list[list[str]]) -> dict[str, int]:
    """Для каждого атакующего типа — сколько покемонов в команде уязвимы.

    team_types — список списков типов (у каждого покемона свой список).
    Возвращает {атакующий_тип: количество_уязвимых_покемонов}.
    """
    summary: dict[str, int] = {}
    for types in team_types:
        for attack_type in weaknesses_of(types):
            summary[attack_type] = summary.get(attack_type, 0) + 1
    return summary