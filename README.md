# K8s Debug Assistant

Simple Streamlit UI that runs a small LangGraph StateGraph to detect common Kubernetes pod failures from pasted logs.

## What it does
- Detects common pod failure types (CrashLoopBackOff, OOMKilled, CreateContainerConfigError)
- Optionally runs LLM analysis (ChatGroq) if you provide a Groq API key
- Produces a short root-cause summary, extracted signals, remediation steps, and kubectl commands

## How it works
- `app.py` is the Streamlit UI entrypoint.
- `graph.py` contains the logic that runs the LangGraph StateGraph and returns a structured report.
- `samples.py` provides example log snippets you can pick from.

## Quick start
1. Create and activate a virtual environment (Windows PowerShell example):

```powershell
python -m venv .venv
& .venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Run the app locally (Streamlit):

```powershell
python -m streamlit run app.py --server.port 8501
```

Then open http://localhost:8501 in your browser.

## How to use
- Paste kubectl `describe` or `logs` output into the "PASTE LOGS" tab.
- Or pick a sample from the "SAMPLES" tab to try the analysis.
- Click the **Run LangGraph Analysis →** button to run detection and (optionally) LLM analysis.
- If using LLM analysis, enter your Groq API key in the sidebar.

Note: The upload controls were removed per workspace preferences — use paste or samples.

## Troubleshooting
- If Streamlit warns about accessibility, the app hides labels using `label_visibility='collapsed'` intentionally.
- If the server port 8501 is already in use, change `--server.port` to another free port.

## Files
- `app.py` — Streamlit UI
- `graph.py` — graph runner logic
- `samples.py` — example logs

paste some logs and press Run!
