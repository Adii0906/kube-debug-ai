# detector.py
# Deterministic pattern detection — Node 1 of the LangGraph graph.
# Pure Python / regex, no external dependencies.

import re
from state import AgentState


def detect_node(state: AgentState) -> AgentState:
    """
    LangGraph Node 1 — Pattern Detection.
    Reads:  state["raw_logs"]
    Writes: failure_type, is_root_cause, signals, confidence, route
    """
    logs = state["raw_logs"].strip()

    if not logs:
        state["error"] = "No log content provided."
        state["route"] = "unknown"
        return state

    # Run detectors in priority order (OOM & config are true root causes)
    result = _detect_oom(logs) or _detect_config_error(logs) or _detect_crashloop(logs)

    if result:
        state["failure_type"]  = result["failure_type"]
        state["is_root_cause"] = result["is_root_cause"]
        state["signals"]       = result["signals"]
        state["confidence"]    = result["confidence"]
        state["route"]         = "analyze"
    else:
        state["failure_type"]  = None
        state["is_root_cause"] = False
        state["signals"]       = {}
        state["confidence"]    = "low"
        state["route"]         = "unknown"

    return state


# ── OOMKilled / Exit 137 ──────────────────────────────────────────────────────

def _detect_oom(logs: str) -> dict | None:
    patterns = [
        r"OOMKilled",
        r"[Ee]xit\s*[Cc]ode[:\s]+137",
        r"exit status 137",
        r"reason:\s*OOMKilled",
        r"Out of memory",
        r"oom_kill",
    ]
    if not any(re.search(p, logs, re.IGNORECASE) for p in patterns):
        return None

    signals = {}

    m = re.search(r"[Ll]imits?[\s\S]{0,40}memory[:\s]+(\S+)", logs)
    if m: signals["memory_limit"] = m.group(1)

    m = re.search(r"[Rr]equests?[\s\S]{0,40}memory[:\s]+(\S+)", logs)
    if m: signals["memory_request"] = m.group(1)

    m = re.search(r"[Rr]estart\s+[Cc]ount[:\s]+(\d+)", logs)
    if m: signals["restart_count"] = m.group(1)

    if re.search(r"java\.lang\.OutOfMemoryError|GC overhead limit", logs):
        signals["oom_type"] = "JVM heap exhaustion"
    else:
        signals["oom_type"] = "container memory limit breached"

    if re.search(r"Killed process|oom_kill_process", logs):
        signals["kernel_oom"] = "true"

    return {
        "failure_type":  "OOMKilled / Exit Code 137",
        "is_root_cause": True,
        "confidence":    "high",
        "signals":       signals,
    }


# ── CreateContainerConfigError ────────────────────────────────────────────────

def _detect_config_error(logs: str) -> dict | None:
    patterns = [
        r"CreateContainerConfigError",
        r"secret[\"']?\s+not found",
        r"configmap[\"']?\s+not found",
        r"references non-existent secret",
        r"couldn't find key",
        r"invalid.*env",
    ]
    if not any(re.search(p, logs, re.IGNORECASE) for p in patterns):
        return None

    signals = {}

    if re.search(r"[Ss]ecret", logs):
        signals["missing_resource"] = "Secret"
        m = re.search(r'secret[s]?["\s:/]+([a-z0-9][a-z0-9\-]+)', logs, re.IGNORECASE)
        if m: signals["resource_name"] = m.group(1)

    if re.search(r"[Cc]onfig[Mm]ap", logs):
        signals["missing_resource"] = "ConfigMap"
        m = re.search(r'configmap[s]?["\s:/]+([a-z0-9][a-z0-9\-]+)', logs, re.IGNORECASE)
        if m: signals["resource_name"] = m.group(1)

    m = re.search(r"namespace[:\s]+([a-z0-9\-]+)", logs, re.IGNORECASE)
    if m: signals["namespace"] = m.group(1)

    if re.search(r"\benv\b|environment", logs):
        signals["env_var_issue"] = "true"

    return {
        "failure_type":  "CreateContainerConfigError",
        "is_root_cause": True,
        "confidence":    "high",
        "signals":       signals,
    }


# ── CrashLoopBackOff ──────────────────────────────────────────────────────────

def _detect_crashloop(logs: str) -> dict | None:
    patterns = [
        r"CrashLoopBackOff",
        r"[Bb]ack-?[Oo]ff restarting",
    ]
    if not any(re.search(p, logs, re.IGNORECASE) for p in patterns):
        return None

    signals = {}

    m = re.search(r"[Rr]estart\s+[Cc]ount[:\s]+(\d+)", logs)
    if m:
        signals["restart_count"] = m.group(1)
        if int(m.group(1)) > 5:
            signals["severity_hint"] = f"high — restarted {m.group(1)} times"

    m = re.search(r"[Ee]xit\s+[Cc]ode[:\s]+(\d+)", logs)
    if m:
        code = m.group(1)
        signals["exit_code"] = code
        exit_map = {
            "1":   "application startup error",
            "2":   "shell misuse / bad argument",
            "137": "SIGKILL — likely OOMKilled",
        }
        signals["likely_cause"] = exit_map.get(code, f"non-zero exit ({code})")

    m = re.search(r"[Rr]eason[:\s]+(\w+)", logs)
    if m: signals["termination_reason"] = m.group(1)

    return {
        "failure_type":  "CrashLoopBackOff",
        "is_root_cause": False,          # symptom — deeper cause needed
        "confidence":    "high",
        "signals":       signals,
    }
