"""REST backend:  uvicorn api:app --reload"""
from fastapi import FastAPI
from pydantic import BaseModel
from troubleshooter.agent import TroubleshootingAgent
from troubleshooter.feedback import save_analysis, add_feedback, stats

app = FastAPI(title="Deployment Troubleshooting Assistant", version="1.0.0")
agent = TroubleshootingAgent()


class LogIn(BaseModel):
    log_text: str


class FeedbackIn(BaseModel):
    analysis_id: str
    useful: bool
    correct_category: str | None = None
    comment: str = ""


@app.get("/health")
def health(): return {"status": "ok", "engine": agent.classifier.backend, "llm": agent.provider}


@app.post("/analyze")
def analyze(body: LogIn):
    r = agent.analyze(body.log_text); save_analysis(r); return r.to_dict()


@app.post("/feedback")
def feedback(body: FeedbackIn):
    add_feedback(body.analysis_id, body.useful, body.correct_category, body.comment); return {"ok": True}


@app.get("/stats")
def get_stats(): return stats()
