"""Streamlit dashboard:  streamlit run app.py"""
import streamlit as st
import plotly.express as px
from pathlib import Path
from troubleshooter.agent import TroubleshootingAgent
from troubleshooter.config import DATA_DIR
from troubleshooter.feedback import save_analysis, add_feedback, stats
from troubleshooter.report import to_markdown

st.set_page_config(page_title="Deployment Troubleshooting Assistant", page_icon="🛠️", layout="wide")


@st.cache_resource
def get_agent(use_llm: bool):
    return TroubleshootingAgent(use_llm=use_llm)


with st.sidebar:
    st.header("Settings")
    use_llm = st.toggle("Use GenAI (LangChain LLM)", value=True, help="Needs an API key in .env; otherwise runs offline with templates")
    agent = get_agent(use_llm)
    st.caption(f"Engine: **{agent.classifier.backend}** + **{agent.provider if agent.reasoner else 'template'}**")
    s = stats()
    st.metric("Usefulness feedback", f"{s['usefulness_pct']}%" if s["usefulness_pct"] is not None else "n/a",
              help=f"{s['useful']} useful of {s['feedback']} ratings (target: 80%+)")

st.title("🛠️ Deployment Issue Troubleshooting Assistant")
st.write("Upload or paste a deployment/CI log. The agent parses it, classifies the failure, finds the root cause and recommends fixes.")

samples = {p.stem.replace("_", " ").title(): p for p in sorted((DATA_DIR / "sample_logs").glob("*.log"))}
c1, c2 = st.columns([2, 1])
with c2:
    up = st.file_uploader("Upload log", type=["log", "txt", "out"])
    pick = st.selectbox("…or load a sample", ["—"] + list(samples))
text = ""
if up: text = up.read().decode("utf-8", errors="replace")
elif pick != "—": text = samples[pick].read_text()
with c1:
    text = st.text_area("Log text", value=text, height=260)

if st.button("Analyze", type="primary", disabled=not text.strip()):
    with st.spinner("Agent working…"):
        st.session_state["r"] = agent.analyze(text); save_analysis(st.session_state["r"])

r = st.session_state.get("r")
if r:
    st.divider()
    a, b, c, d = st.columns(4)
    a.metric("Issue type", r.issue_type); b.metric("Severity", r.severity)
    c.metric("Confidence", f"{r.confidence:.0%}"); d.metric("Response time", f"{r.latency_s}s")
    if r.needs_human_review: st.warning("Low confidence — please have an engineer review this result.")
    st.subheader("Summary"); st.write(r.summary)
    l, rt = st.columns(2)
    with l:
        st.subheader("Probable causes"); _ = [st.markdown(f"{i}. {x}") for i, x in enumerate(r.probable_causes, 1)]
        st.subheader("Validation steps"); _ = [st.markdown(f"- {x}") for x in r.validation_steps]
    with rt:
        st.subheader("Recommended actions"); _ = [st.markdown(f"{i}. {x}") for i, x in enumerate(r.recommended_actions, 1)]
    st.subheader("Critical errors")
    import pandas as pd
    st.dataframe(pd.DataFrame(r.evidence), use_container_width=True, hide_index=True)
    lv = {"Errors": r.stats["errors"], "Warnings": r.stats["warnings"],
          "Other": r.stats["total_lines"] - r.stats["errors"] - r.stats["warnings"]}
    st.plotly_chart(px.bar(x=list(lv), y=list(lv.values()), labels={"x": "", "y": "lines"}, title="Log composition"), use_container_width=True)
    with st.expander("Agent trace (how the answer was produced)"):
        st.table(pd.DataFrame(r.trace))
    st.download_button("⬇ Download troubleshooting report", to_markdown(r), file_name=f"report_{r.id}.md")
    st.subheader("Was this useful?")
    f1, f2, f3 = st.columns([1, 1, 3])
    cats = ["(correct)"] + agent.kb.labels
    fix = f3.selectbox("If the category is wrong, pick the right one", cats)
    if f1.button("👍 Useful"): add_feedback(r.id, True, None if fix == "(correct)" else fix); st.toast("Thanks!")
    if f2.button("👎 Not useful"): add_feedback(r.id, False, None if fix == "(correct)" else fix); st.toast("Thanks — logged for retraining")
