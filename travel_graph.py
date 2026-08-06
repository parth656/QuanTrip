from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, START, END

from travel_tools import (
    orchestrator,
    ask_missing_value,
    rag_search,
    recommend_places,
    partial_response_node,
    estimate_budget,
    generate_itinerary,
    group_plan,
    final_response_node
)


class TripState(TypedDict, total=False):
    destination: str
    interests: List[str]
    days: int
    travelers: int
    budget_type: str
    members: List[Dict[str, Any]]

    missing_fields: List[str]
    next_step: str

    retrieved_context: List[Dict[str, Any]]
    recommended_places: List[Dict[str, Any]]
    budget_breakdown: Dict[str, Any]
    itinerary: Dict[str, Any]
    group_plan_result: Dict[str, Any]
    final_response: Dict[str, Any]


def route_from_orchestrator(state: TripState) -> str:
    if state.get("next_step") == "ask_missing_value":
        return "ask_missing_value"

    return "rag_search"


def route_after_recommendation(state: TripState) -> str:
    missing_fields = state.get("missing_fields", [])

    required_for_full_plan = [
        "days",
        "travelers",
        "budget_type"
    ]

    for field in required_for_full_plan:
        if field in missing_fields:
            return "partial_response"

    return "estimate_budget"


def build_trip_graph():
    graph = StateGraph(TripState)

    graph.add_node("orchestrator", orchestrator)
    graph.add_node("ask_missing_value", ask_missing_value)

    graph.add_node("rag_search", rag_search)
    graph.add_node("recommend_places", recommend_places)
    graph.add_node("partial_response", partial_response_node)

    graph.add_node("estimate_budget", estimate_budget)
    graph.add_node("generate_itinerary", generate_itinerary)
    graph.add_node("group_plan", group_plan)
    graph.add_node("final_response", final_response_node)

    graph.add_edge(START, "orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "ask_missing_value": "ask_missing_value",
            "rag_search": "rag_search"
        }
    )

    graph.add_edge("ask_missing_value", END)

    graph.add_edge("rag_search", "recommend_places")

    graph.add_conditional_edges(
        "recommend_places",
        route_after_recommendation,
        {
            "partial_response": "partial_response",
            "estimate_budget": "estimate_budget"
        }
    )

    graph.add_edge("partial_response", END)

    graph.add_edge("estimate_budget", "generate_itinerary")
    graph.add_edge("generate_itinerary", "group_plan")
    graph.add_edge("group_plan", "final_response")
    graph.add_edge("final_response", END)

    return graph.compile()


trip_graph = build_trip_graph()


def run_trip_workflow(input_data: Dict[str, Any]) -> Dict[str, Any]:
    initial_state = {
        "destination": input_data.get("destination", ""),
        "interests": input_data.get("interests", []),
        "days": input_data.get("days", 0),
        "travelers": input_data.get("travelers", 0),
        "budget_type": input_data.get("budget_type", ""),
        "members": input_data.get("members", []),

        "missing_fields": [],
        "next_step": "",

        "retrieved_context": [],
        "recommended_places": [],
        "budget_breakdown": {},
        "itinerary": {},
        "group_plan_result": {},
        "final_response": {}
    }

    result = trip_graph.invoke(initial_state)

    return result.get("final_response", {})