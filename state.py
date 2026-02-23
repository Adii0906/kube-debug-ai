# state.py
# Shared AgentState TypedDict — passed between every LangGraph node.
# LangGraph reads/writes this dict as it traverses the graph.

from typing import TypedDict, Optional


class AgentState(TypedDict):
    # ── Inputs ─────────────────────────────────────────────────────────
    raw_logs: str
    groq_api_key: str
    model: str

    # ── Node: detect ────────────────────────────────────────────────────
    failure_type: Optional[str]       # "CrashLoopBackOff" | "OOMKilled" | "CreateContainerConfigError" | None
    is_root_cause: Optional[bool]     # True = root cause, False = symptom
    signals: Optional[dict]           # Extracted key signals from logs
    confidence: Optional[str]         # "high" | "medium" | "low"

    # ── Node: analyze ───────────────────────────────────────────────────
    root_cause: Optional[str]
    explanation: Optional[str]
    severity: Optional[str]
    remediation_steps: Optional[list]
    kubectl_commands: Optional[list]

    # ── Node: format ────────────────────────────────────────────────────
    final_report: Optional[dict]

    # ── Routing / error ─────────────────────────────────────────────────
    route: Optional[str]              # used by conditional edge: "analyze" | "unknown"
    error: Optional[str]
