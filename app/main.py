import re
import time

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.analyzer import review
from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.db import ReviewRecord, User, get_db, init_db
from app.github_review import GitHubReviewError, review_pull_request
from app.llm import explain_findings
from app.metrics import REVIEW_DURATION, REVIEW_FINDINGS, REVIEWS_TOTAL, metrics_response
from app.models import Finding, ReviewRequest, ReviewResponse

app = FastAPI(title="AI Code Review & Bug Detection Platform", version="3.0.0")
init_db()


class AuthRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=128)


def normalize_email(email: str) -> str:
    email = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Invalid email address")
    return email


@app.get("/", include_in_schema=False)
def home():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "code-review-api"}


@app.get("/metrics")
def metrics():
    body, media_type = metrics_response()
    return Response(content=body, media_type=media_type)


@app.post("/api/v1/auth/register")
def register(request: AuthRequest, db: Session = Depends(get_db)):
    email = normalize_email(request.email)
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, password_hash=hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user), "token_type": "bearer"}


@app.post("/api/v1/auth/login")
def login(request: AuthRequest, db: Session = Depends(get_db)):
    email = normalize_email(request.email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_access_token(user), "token_type": "bearer"}


@app.get("/api/v1/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}


@app.post("/api/v1/review", response_model=ReviewResponse)
def create_review(
    request: ReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    started = time.perf_counter()
    score, findings = review(request.code, request.language)
    items = [Finding(**f.__dict__) for f in findings]
    summary = "No issues detected." if not items else f"Detected {len(items)} potential issue(s)."
    REVIEWS_TOTAL.labels(request.language).inc()
    for finding in items:
        REVIEW_FINDINGS.labels(finding.severity).inc()
    REVIEW_DURATION.observe(time.perf_counter() - started)
    db.add(ReviewRecord(user_id=user.id, language=request.language, score=score, finding_count=len(items), summary=summary, code=request.code))
    db.commit()
    return ReviewResponse(score=score, summary=summary, findings=items)


@app.get("/api/v1/reviews")
def review_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ReviewRecord).filter(ReviewRecord.user_id == user.id).order_by(ReviewRecord.id.desc()).limit(50).all()
    return [{"id": r.id, "language": r.language, "score": r.score, "finding_count": r.finding_count, "summary": r.summary, "created_at": r.created_at} for r in rows]


@app.post("/api/v1/review/explain")
def explain_review(request: ReviewRequest, user: User = Depends(get_current_user)):
    score, findings = review(request.code, request.language)
    payload = [f.__dict__ for f in findings]
    return {"score": score, "findings": payload, "explanation": explain_findings(request.code, payload)}


@app.get("/api/v1/github/{repo_owner}/{repo_name}/pulls/{pr_number}/review")
def github_pr_review(repo_owner: str, repo_name: str, pr_number: int, user: User = Depends(get_current_user)):
    try:
        return review_pull_request(f"{repo_owner}/{repo_name}", pr_number)
    except GitHubReviewError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub review failed: {exc}") from exc
