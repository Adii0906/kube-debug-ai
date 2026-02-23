# nodes.py
# LangGraph Node functions (Nodes 2 and 3).
# Each function: AgentState → AgentState

import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from state import AgentState


# ── Node 2: analyze_node  (calls Groq via LangChain) ─────────────────────────

def analyze_node(state: AgentState) -> AgentState:
    """
    LangGraph Node 2 — LLM Root Cause Analysis.
    Uses LangChain's ChatGroq to call Groq API.
    Reads:  failure_type, signals, raw_logs
    Writes: root_cause, explanation, severity, remediation_steps, kubectl_commands
    """
    failure_type = state["failure_type"]
    signals      = state.get("signals", {})
    is_root      = state.get("is_root_cause", False)
    logs_preview = state["raw_logs"][:2500]
    api_key      = state["groq_api_key"]
    model        = state.get("model", "llama-3.3-70b-versatile")

    signal_text = "\n".join(f"  - {k}: {v}" for k, v in signals.items()) or "  None detected"

    system_msg = SystemMessage(content=(
        "You are a Kubernetes SRE expert. "
        "Respond ONLY with a valid JSON object — no markdown, no extra text."
    ))

    human_msg = HumanMessage(content=f"""Analyze this Kubernetes failure and respond with structured JSON.

## Detected Failure
{failure_type}

## Is It Root Cause or Symptom?
{"ROOT CAUSE" if is_root else "SYMPTOM — there is a deeper underlying issue"}

## Extracted Signals
{signal_text}

## Log Excerpt
```
{logs_preview}
```

Respond ONLY with this JSON structure:
{{
  "root_cause": "one clear sentence — the actual root cause",
  "explanation": "2-3 plain-English sentences explaining what happened",
  "severity": "critical" | "high" | "medium",
  "remediation_steps": [
    "Step 1: specific action",
    "Step 2: specific action",
    "Step 3: specific action"
  ],
  "kubectl_commands": [
    "kubectl command with <placeholders>",
    "kubectl command with <placeholders>"
  ]
}}""")

    try:
        llm = ChatGroq(
            api_key=api_key,
            model=model,
            temperature=0.1,
            max_tokens=800,
        )

        response = llm.invoke([system_msg, human_msg])
        content  = response.content.strip()

        # Strip markdown fences if model added them
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        parsed = json.loads(content.strip())

        state["root_cause"]         = parsed.get("root_cause", "")
        state["explanation"]        = parsed.get("explanation", "")
        state["severity"]           = parsed.get("severity", "high")
        state["remediation_steps"]  = parsed.get("remediation_steps", [])
        state["kubectl_commands"]   = parsed.get("kubectl_commands", [])

    except Exception as e:
        # Graceful fallback — pattern results still shown
        state["root_cause"]        = f"LLM error: {str(e)[:120]}"
        state["explanation"]       = "Add a valid Groq API key for AI analysis. Pattern detection results are shown."
        state["severity"]          = "high"
        state["remediation_steps"] = _fallback_steps(failure_type)
        state["kubectl_commands"]  = _fallback_cmds(failure_type)

    return state


# ── Node 3: format_node  (assembles final report) ─────────────────────────────

def format_node(state: AgentState) -> AgentState:
    """
    LangGraph Node 3 — Report Assembler.
    Merges all node outputs into state["final_report"].
    """
    state["final_report"] = {
        "failure_type":      state.get("failure_type", "Unknown"),
        "is_root_cause":     state.get("is_root_cause", False),
        "confidence":        state.get("confidence", "low"),
        "signals":           state.get("signals", {}),
        "root_cause":        state.get("root_cause", ""),
        "explanation":       state.get("explanation", ""),
        "severity":          state.get("severity", "high"),
        "remediation_steps": state.get("remediation_steps", []),
        "kubectl_commands":  state.get("kubectl_commands", []),
    }
    return state


# ── Node: unknown_node  (no pattern matched) ──────────────────────────────────

def unknown_node(state: AgentState) -> AgentState:
    """
    Fallback node when no known failure pattern is detected.
    Reached via conditional edge when route == "unknown".
    """
    state["final_report"] = {
        "failure_type":  "No known pattern detected",
        "is_root_cause": False,
        "confidence":    "low",
        "signals":       {},
        "root_cause":    "The logs did not match CrashLoopBackOff, OOMKilled, or CreateContainerConfigError.",
        "explanation":   "Try pasting kubectl describe output or pod logs that contain Events, State, or Reason fields.",
        "severity":      "unknown",
        "remediation_steps": [
            "Run: kubectl describe pod <pod-name> -n <namespace>",
            "Run: kubectl logs <pod-name> --previous -n <namespace>",
            "Check cluster events: kubectl get events -n <namespace> --sort-by=.lastTimestamp",
        ],
        "kubectl_commands": [
            "kubectl get pods -n <namespace> -o wide",
            "kubectl describe pod <pod-name> -n <namespace>",
        ],
    }
    return state


# ── Conditional routing function ──────────────────────────────────────────────

def route_after_detect(state: AgentState) -> str:
    """
    LangGraph conditional edge function.
    Called after detect_node to decide next node.
    Returns: "analyze" | "unknown"
    """
    return state.get("route", "unknown")


# ── Fallback helpers ─────────────────────────────────────────────────────────

def _fallback_steps(failure_type: str) -> list:
    return {
        "OOMKilled / Exit Code 137": [
            "Increase resources.limits.memory in the pod spec",
            "Profile app memory usage to find leaks",
            "Consider Vertical Pod Autoscaler (VPA)",
        ],
        "CrashLoopBackOff": [
            "Run: kubectl logs <pod> --previous to see crash reason",
            "Check all env vars, secrets, and configmaps are present",
            "Verify startup command and entrypoint are correct",
        ],
        "CreateContainerConfigError": [
            "Verify the Secret or ConfigMap exists: kubectl get secrets,configmaps -n <ns>",
            "Check spelling of names in the pod spec envFrom / env sections",
            "Create the missing resource if it doesn't exist",
        ],
    }.get(failure_type, ["Check kubectl describe pod and kubectl logs for clues"])


def _fallback_cmds(failure_type: str) -> list:
    return {
        "OOMKilled / Exit Code 137": [
            "kubectl top pods -n <namespace>",
            "kubectl describe pod <pod> -n <namespace>",
        ],
        "CrashLoopBackOff": [
            "kubectl logs <pod> --previous -n <namespace>",
            "kubectl describe pod <pod> -n <namespace>",
        ],
        "CreateContainerConfigError": [
            "kubectl get secrets,configmaps -n <namespace>",
            "kubectl describe pod <pod> -n <namespace>",
        ],
    }.get(failure_type, ["kubectl describe pod <pod> -n <namespace>"])
