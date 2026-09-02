from fastapi import FastAPI, HTTPException
from app.analyzer import review
from app.github_review import GitHubReviewError, review_pull_request
from app.llm import explain_findings
from app.models import Finding, ReviewRequest, ReviewResponse

app = FastAPI(title="AI Code Review & Bug Detection Platform", version="2.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/review", response_model=ReviewResponse)
def create_review(request: ReviewRequest):
    score, findings = review(request.code, request.language)
    items = [Finding(**f.__dict__) for f in findings]
    summary = "No issues detected." if not items else f"Detected {len(items)} potential issue(s)."
    return ReviewResponse(score=score, summary=summary, findings=items)


@app.post("/api/v1/review/explain")
def explain_review(request: ReviewRequest):
    score, findings = review(request.code, request.language)
    payload = [f.__dict__ for f in findings]
    return {"score": score, "findings": payload, "explanation": explain_findings(request.code, payload)}


@app.get("/api/v1/github/{repo_owner}/{repo_name}/pulls/{pr_number}/review")
def github_pr_review(repo_owner: str, repo_name: str, pr_number: int):
    try:
        return review_pull_request(f"{repo_owner}/{repo_name}", pr_number)
    except GitHubReviewError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub review failed: {exc}") from exc
