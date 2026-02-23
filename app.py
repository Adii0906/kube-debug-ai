# app.py
# Streamlit UI — entry point.
# All analysis goes through graph.py which uses the real LangGraph StateGraph.

import os
from pathlib import Path
import streamlit as st
from graph import run_graph, compiled_graph
from samples import SAMPLES

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="K8s Debug Assistant",
    page_icon="🔬",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #f4f1ea !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    color: #1a1a1a !important;
}
[data-testid="stSidebar"] {
    background: #111 !important;
    border-right: none !important;
}
[data-testid="stSidebar"] * { color: #ddd !important; }
[data-testid="stSidebar"] label {
    color: #555 !important; font-size: 0.68rem !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
}
[data-testid="stSidebar"] input {
    background: #222 !important; border: 1px solid #333 !important;
    color: #ddd !important; font-family: 'IBM Plex Mono', monospace !important;
}
[data-baseweb="select"] > div {
    background: #222 !important; border-color: #333 !important;
}

/* Header */
.title    { font-family:'IBM Plex Mono',monospace; font-size:1.5rem; font-weight:600; color:#111; }
.subtitle { font-family:'IBM Plex Mono',monospace; font-size:0.68rem; color:#888;
            letter-spacing:0.18em; text-transform:uppercase; margin-top:0.2rem; margin-bottom:1.4rem; }

/* Graph diagram in sidebar */
.graph-box {
    background:#1a1a1a; border:1px solid #2a2a2a; border-radius:6px;
    padding:0.9rem 1rem; font-family:'IBM Plex Mono',monospace; font-size:0.68rem;
    color:#aaa; line-height:1.9; margin-top:0.5rem;
}
.gnode { color:#7dff94; }
.gedge { color:#555; }

/* Result cards */
.card {
    background:white; border:1px solid #e2ddd4; border-radius:6px;
    padding:1.1rem 1.3rem; margin:0.5rem 0;
}
.card-label {
    font-family:'IBM Plex Mono',monospace; font-size:0.6rem;
    letter-spacing:0.2em; text-transform:uppercase; color:#999; margin-bottom:0.5rem;
}
.root-cause-box {
    border-left:3px solid #111; padding-left:0.9rem;
    font-size:0.98rem; font-weight:500; color:#111; line-height:1.55;
}
.explanation-text {
    font-size:0.83rem; color:#555; line-height:1.65; margin-top:0.7rem;
}

/* Severity badge */
.badge {
    display:inline-block; font-family:'IBM Plex Mono',monospace;
    font-size:0.68rem; font-weight:600; padding:0.22rem 0.75rem;
    border-radius:3px; margin-right:0.4rem;
}
.badge-critical { background:#fee; color:#c00; border:1px solid #fcc; }
.badge-high     { background:#fff3e0; color:#e65100; border:1px solid #ffe0b2; }
.badge-medium   { background:#fffde7; color:#f57f17; border:1px solid #fff9c4; }
.badge-cause    { background:#111; color:#f4f1ea; }
.badge-symptom  { background:#e8e4dc; color:#555; }

/* Signals */
.sig-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:0.38rem 0; border-bottom:1px solid #f0ece4;
}
.sig-key { font-family:'IBM Plex Mono',monospace; font-size:0.72rem; color:#888; }
.sig-val { font-family:'IBM Plex Mono',monospace; font-size:0.72rem; color:#111; font-weight:500; }

/* Steps */
.step {
    display:flex; gap:0.7rem; padding:0.55rem 0;
    border-bottom:1px solid #f0ece4; align-items:flex-start;
}
.step-n {
    font-family:'IBM Plex Mono',monospace; font-size:0.65rem;
    background:#111; color:white; border-radius:50%;
    min-width:21px; height:21px; display:flex;
    align-items:center; justify-content:center; flex-shrink:0; margin-top:1px;
}
.step-t { font-size:0.82rem; color:#333; line-height:1.5; }

/* Command */
.cmd {
    background:#111; color:#7dff94; font-family:'IBM Plex Mono',monospace;
    font-size:0.75rem; padding:0.55rem 0.9rem; border-radius:4px; margin:0.3rem 0;
}

/* Streamlit overrides */
.stTextArea textarea {
    background:white !important; border:1px solid #ddd9d0 !important;
    border-radius:6px !important; font-family:'IBM Plex Mono',monospace !important;
    font-size:0.77rem !important; color:#111 !important;
}
.stTextArea textarea:focus { border-color:#111 !important; box-shadow:none !important; }
.stButton > button {
    background:#111 !important; color:#f4f1ea !important; border:none !important;
    border-radius:4px !important; font-family:'IBM Plex Mono',monospace !important;
    font-size:0.78rem !important; letter-spacing:0.06em !important;
    padding:0.55rem 1.4rem !important; font-weight:500 !important;
}
.stButton > button:hover { opacity:0.82 !important; }
.stTabs [data-baseweb="tab"] {
    font-family:'IBM Plex Mono',monospace !important; font-size:0.7rem !important;
}
div[data-testid="stExpander"] details {
    background:white !important; border:1px solid #ddd9d0 !important; border-radius:6px !important;
}
label {
    font-family:'IBM Plex Mono',monospace !important; font-size:0.68rem !important;
    letter-spacing:0.1em !important; text-transform:uppercase !important; color:#777 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.95rem;font-weight:600;
         padding:0.4rem 0 1.1rem;border-bottom:1px solid #222;margin-bottom:1rem;">
         K8s Debug Assistant
    </div>""", unsafe_allow_html=True)

    # Load optional .env file (project root) and prefill Groq API key if present.
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                # only set if not already present in environment
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    default_groq = os.getenv("GROQ_API_KEY", "")

    groq_api_key = st.text_input(
        "Groq API Key",
        value=default_groq,
        type="password",
        placeholder="gsk_...",
        help="Free at console.groq.com (or put in .env as GROQ_API_KEY)",
    )
    model = st.selectbox(
        "Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    )

    st.markdown("---")

    # Real LangGraph graph topology
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;
         color:#555;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:0.5rem;">
         LangGraph topology
    </div>
    <div class="graph-box">
<span class="gedge">START</span>
  <span class="gedge">└──►</span> <span class="gnode">detect_node</span>
        <span class="gedge">├──(analyze)──►</span>
        <span class="gnode">analyze_node</span>
              <span class="gedge">└──►</span> <span class="gnode">format_node</span>
                    <span class="gedge">└──► END</span>
        <span class="gedge">└──(unknown)──►</span>
        <span class="gnode">unknown_node</span>
              <span class="gedge">└──► END</span>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;
         color:#555;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:0.5rem;">
         Detects
    </div>""", unsafe_allow_html=True)
    for label in ["CrashLoopBackOff", "OOMKilled / Exit 137", "CreateContainerConfigError"]:
        st.markdown(f"""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;
             color:#666;padding:0.2rem 0;">
             <span style="color:#7dff94;">✓</span> {label}
        </div>""", unsafe_allow_html=True)

    # (Upload UI removed)

# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="title">K8s Debug Assistant</div>', unsafe_allow_html=True)
st.markdown("""
<div class="subtitle">
    LangGraph StateGraph &nbsp;·&nbsp; LangChain ChatGroq &nbsp;·&nbsp;
    Streamlit &nbsp;·&nbsp; 4-node conditional graph
</div>""", unsafe_allow_html=True)

# ── Input ──────────────────────────────────────────────────────────────────────
col_in, col_info = st.columns([3, 2], gap="large")

with col_in:
    tab_paste, tab_sample = st.tabs(["PASTE LOGS", "SAMPLES"])
    log_text = ""

    with tab_paste:
        v = st.text_area(
            "Paste logs",
            height=280,
            placeholder="Paste kubectl describe, pod logs, or events output here…",
            label_visibility="collapsed",
        )
        if v: log_text = v

    with tab_sample:
        pick = st.selectbox("Choose sample", ["— pick —"] + list(SAMPLES.keys()), label_visibility="collapsed")
        if pick != "— pick —":
            log_text = SAMPLES[pick]
            st.code(log_text[:500] + "…", language="bash")

with col_info:
    st.markdown("""
    <div class="card">
    <div class="card-label">How the graph runs</div>""", unsafe_allow_html=True)

    for n, title, desc in [
        (1, "detect_node",  "Regex pattern detection → sets route = 'analyze' or 'unknown'"),
        (2, "analyze_node", "LangChain ChatGroq → structured JSON root cause + remediation"),
        (3, "format_node",  "Merges all node outputs into final_report"),
        (4, "unknown_node", "Fallback when no failure pattern matched (conditional edge)"),
    ]:
        st.markdown(f"""
        <div class="step" style="border-bottom:1px solid #f0ece4;">
            <div class="step-n">{n}</div>
            <div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;
                     color:#111;font-weight:500;">{title}</div>
                <div style="font-size:0.77rem;color:#777;margin-top:0.1rem;line-height:1.4;">
                    {desc}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Run button ─────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
_, bc, _ = st.columns([1, 1.4, 1])
with bc:
    run = st.button("Run LangGraph Analysis →", use_container_width=True)

# ── Analysis & Results ─────────────────────────────────────────────────────────
if run:
    if not log_text.strip():
        st.error("Paste logs, upload a file, or pick a sample first.")
        st.stop()

    if not groq_api_key:
        st.warning("No Groq API key — using pattern detection only. Add your key for LLM analysis.")

    with st.spinner("Running LangGraph graph…"):
        report = run_graph(
            raw_logs=log_text,
            groq_api_key=groq_api_key or "",
            model=model,
        )

    if not report:
        st.error("Analysis returned no result.")
        st.stop()

    st.markdown("---")

    # ── Header row ─────────────────────────────────────────────────────────────
    failure  = report.get("failure_type", "Unknown")
    severity = report.get("severity", "high")
    is_root  = report.get("is_root_cause", False)
    conf     = report.get("confidence", "low")

    sev_cls = {"critical": "badge-critical", "high": "badge-high", "medium": "badge-medium"}.get(severity, "badge-high")

    st.markdown(f"""
    <div style="margin-bottom:1rem;">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:1rem;font-weight:600;
             color:#111;margin-bottom:0.5rem;">{failure}</div>
        <span class="badge {'badge-cause' if is_root else 'badge-symptom'}">
            {'⬤ Root Cause' if is_root else '◎ Symptom'}
        </span>
        <span class="badge {sev_cls}">{severity.upper()}</span>
        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
              color:#aaa;margin-left:0.3rem;">detection confidence: {conf}</span>
    </div>""", unsafe_allow_html=True)

    # ── Two-column results ──────────────────────────────────────────────────────
    left, right = st.columns(2, gap="medium")

    with left:
        # Root cause + explanation
        st.markdown(f"""
        <div class="card">
            <div class="card-label">Root Cause</div>
            <div class="root-cause-box">{report.get('root_cause', '—')}</div>
            <div class="explanation-text">{report.get('explanation', '')}</div>
        </div>""", unsafe_allow_html=True)

        # Extracted signals
        signals = report.get("signals") or {}
        if signals:
            st.markdown('<div class="card"><div class="card-label">Extracted Signals</div>',
                        unsafe_allow_html=True)
            for k, v in signals.items():
                st.markdown(f"""
                <div class="sig-row">
                    <span class="sig-key">{k.replace('_',' ').title()}</span>
                    <span class="sig-val">{v}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with right:
        # Remediation steps
        steps = report.get("remediation_steps") or []
        if steps:
            st.markdown('<div class="card"><div class="card-label">Remediation Steps</div>',
                        unsafe_allow_html=True)
            for i, step in enumerate(steps, 1):
                st.markdown(f"""
                <div class="step">
                    <div class="step-n">{i}</div>
                    <div class="step-t">{step}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # kubectl commands
        cmds = report.get("kubectl_commands") or []
        if cmds:
            st.markdown('<div class="card" style="margin-top:0;"><div class="card-label">Commands</div>',
                        unsafe_allow_html=True)
            for cmd in cmds:
                st.markdown(f'<div class="cmd">$ {cmd}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # Raw JSON
    with st.expander("Full report JSON"):
        st.json(report)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#ccc;
     text-align:center;padding:2rem 0 0.5rem;letter-spacing:0.1em;">
    langgraph.graph.StateGraph &nbsp;·&nbsp; langchain_groq.ChatGroq
    &nbsp;·&nbsp; add_node / add_edge / add_conditional_edges / compile().invoke()
</div>""", unsafe_allow_html=True)
