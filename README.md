# AI Deployment Issue Troubleshooting Assistant
TCS Technology Day - *IT Application Maintenance: Deployment Issue Troubleshooting Assistant*

A **single-agent** system that accepts deployment/CI logs, finds the probable root cause, and returns a
human-readable summary plus actionable, validated recommendations - via a **Streamlit UI**, **CLI** or **REST API**.

| Required technique | Where it lives |
|---|---|
| **Agentic AI** | `troubleshooter/agent.py` - Plan -> Observe -> Classify -> **Reflect** -> Retrieve -> Generate -> Finalise loop with tool calls, self-reflection (widen context / LLM adjudication / human-review flag) and a full trace. `tools.py` also exposes the tools to an optional LLM-driven LangGraph ReAct agent. |
| **LangChain** | `llm.py` (provider factory), `genai.py` (`prompt \| llm \| parser` chains), `tools.py` (`@tool` definitions, LangGraph agent) |
| **TensorFlow** | `classifier.py` - Keras `TextVectorization -> Embedding -> GlobalAvgPool -> Dense` error classifier, ensembled with KB rules |
| **GenAI** | `genai.py` - log summarisation + recommendation generation grounded in redacted evidence and the runbook; strict JSON output with validation and template fallback |

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # optional: add Azure OpenAI / OpenAI / Anthropic key
python scripts/generate_data.py                         # synthetic logs + training data (already included)
python scripts/train_model.py                           # trains the TensorFlow classifier -> models/
streamlit run app.py                                    # UI  -> http://localhost:8501
python analyzer.py data/sample_logs/database_connectivity.log --trace    # CLI
uvicorn api:app --reload                                # REST -> /docs
python scripts/evaluate.py                              # accuracy / latency on labelled logs
python -m pytest -q                                     # tests
```
**No API key?** Everything still works offline (rules + TensorFlow + template summaries). With a key, the GenAI
layer writes the summary/recommendations and adjudicates ambiguous cases. **No TensorFlow?** It falls back to
scikit-learn automatically (`USE_TENSORFLOW=false` forces this).

## Safety & data handling
* Logs are redacted (passwords, tokens, API keys, emails, IPs, URL credentials) **before** classification or any LLM call.
* The LLM sees only redacted evidence + the matched runbook, must answer in JSON, and invalid output falls back to templates.
* Low-confidence results are flagged **needs human review** instead of guessing.
* Only synthetic data is shipped, per the problem statement.

## Continuous feedback & learning
UI 👍/👎 ratings go to SQLite (`feedback.db`) and drive the **80%+ usefulness** metric. If the user supplies the correct category,
the example is appended to `data/feedback_labels.csv` and included next time you run `scripts/train_model.py`.

## Extending
Add a category by adding an entry to `data/knowledge_base.json` (patterns, causes, fixes, validation) and templates to
`troubleshooter/synth.py`, then re-run `generate_data.py` and `train_model.py`. See `docs/` for the approach write-up, input formats and demo script.

## Honest limitations
* Shipped metrics come from **synthetic** logs. The KB patterns and templates were authored together, so the hybrid's near-100% score is optimistic;
  the ML-only hold-out number printed by `train_model.py` is the better generalisation signal. Validate on real, anonymised logs before claiming the >85% target.
* Docker/Azure deployment files are provided but not deployment-tested.
