# graph.py
# The REAL LangGraph graph — uses StateGraph, add_node, add_edge,
# add_conditional_edges, START, END, and .compile().invoke()

from langgraph.graph import StateGraph, START, END
from state import AgentState
from detector import detect_node
from nodes import analyze_node, format_node, unknown_node, route_after_detect


def build_graph():
    """
    Build and compile the LangGraph StateGraph.

    Graph topology:
        START
          └─► detect_node
                ├─(route="analyze")──► analyze_node ──► format_node ──► END
                └─(route="unknown")──► unknown_node ──────────────────► END
    """
    # 1. Create the graph with our typed state
    graph = StateGraph(AgentState)

    # 2. Register nodes
    graph.add_node("detect",  detect_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("format",  format_node)
    graph.add_node("unknown", unknown_node)

    # 3. Entry edge: START → detect
    graph.add_edge(START, "detect")

    # 4. Conditional edge after detect:
    #    route_after_detect reads state["route"] and returns "analyze" or "unknown"
    graph.add_conditional_edges(
        "detect",
        route_after_detect,
        {
            "analyze": "analyze",
            "unknown": "unknown",
        }
    )

    # 5. Linear edge: analyze → format → END
    graph.add_edge("analyze", "format")
    graph.add_edge("format",  END)

    # 6. unknown node goes straight to END
    graph.add_edge("unknown", END)

    # 7. Compile into a runnable
    return graph.compile()


# Build once at module level — reused across Streamlit reruns
compiled_graph = build_graph()


def run_graph(raw_logs: str, groq_api_key: str, model: str) -> dict:
    """
    Invoke the compiled LangGraph graph.
    Returns final_report dict from the last node.
    """
    initial_state: AgentState = {
        "raw_logs":      raw_logs,
        "groq_api_key":  groq_api_key,
        "model":         model,
        "failure_type":  None,
        "is_root_cause": None,
        "signals":       None,
        "confidence":    None,
        "route":         None,
        "root_cause":    None,
        "explanation":   None,
        "severity":      None,
        "remediation_steps": None,
        "kubectl_commands":  None,
        "final_report":  None,
        "error":         None,
    }

    # .invoke() runs the full graph and returns final state
    final_state = compiled_graph.invoke(initial_state)
    return final_state.get("final_report", {})
