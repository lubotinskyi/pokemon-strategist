"""Сборка графа Pokémon Team Strategist.

Граф:
    parse → fetch → analyze → propose → critic → (final | propose)
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.nodes import (
    analyze_node,
    critic_node,
    fetch_node,
    final_node,
    parse_node,
    propose_node,
)
from src.state import TeamState


def route_after_critic(state: TeamState) -> str:
    """Решить, что делать после критика.

    Возвращает имя следующего узла: "propose" или "final".
    """
    # Если была ошибка — сразу на финал
    if state.get("error"):
        return "final"

    # Если попытки исчерпаны — заканчиваем
    if state.get("attempts", 0) >= state.get("max_attempts", 3):
        return "final"

    # Если замена улучшила команду — заканчиваем
    if state.get("improved"):
        return "final"

    # Иначе — пробуем ещё раз
    return "propose"


def build_graph():
    """Собрать и скомпилировать граф с checkpoint."""
    workflow = StateGraph(TeamState)

    # Узлы
    workflow.add_node("parse", parse_node)
    workflow.add_node("fetch", fetch_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("propose", propose_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("final", final_node)

    # Линейная часть
    workflow.add_edge(START, "parse")
    workflow.add_edge("parse", "fetch")
    workflow.add_edge("fetch", "analyze")
    workflow.add_edge("analyze", "propose")
    workflow.add_edge("propose", "critic")

    # Условное ветвление после критика
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "propose": "propose",
            "final": "final",
        },
    )

    # Финал — конец
    workflow.add_edge("final", END)

    return workflow.compile(checkpointer=MemorySaver())


# Готовый граф — его импортируют main.py и telegram_bot.py
graph = build_graph()