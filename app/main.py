from fastapi import FastAPI
from app.analyzer import review
from app.models import Finding, ReviewRequest, ReviewResponse

app = FastAPI(title="AI Code Review & Bug Detection Platform", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/review", response_model=ReviewResponse)
def create_review(request: ReviewRequest):
    score, findings = review(request.code, request.language)
    items = [Finding(**f.__dict__) for f in findings]
    summary = "No issues detected." if not items else f"Detected {len(items)} potential issue(s)."
    return ReviewResponse(score=score, summary=summary, findings=items)
