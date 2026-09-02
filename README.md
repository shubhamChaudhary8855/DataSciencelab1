# AI Code Review & Bug Detection Platform

An API-first developer tool that reviews Python code for security risks, correctness issues, maintainability problems, and AI-assisted remediation.

## Production-style features
- AST-based Python static analysis
- Security rules for `eval`, `exec`, shell execution, unsafe deserialization, and hard-coded secrets
- Severity scoring and structured findings
- Optional OpenAI-powered explanation/fix plan (`OPENAI_API_KEY`)
- GitHub Pull Request review integration via `GITHUB_TOKEN`
- Interactive browser dashboard
- FastAPI + OpenAPI
- Docker-ready
- Automated tests with GitHub Actions CI

## Architecture
```text
Browser / CI / GitHub PR
        |
     FastAPI
     /     \
Analyzer    GitHub PR Adapter
   |             |
AST + Rules   Changed Python Files
   |             |
Findings ----> Optional LLM Explanation
```

## Run
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/` for the dashboard or `/docs` for the API.

## API
- `POST /api/v1/review` — deterministic static review
- `POST /api/v1/review/explain` — review + optional LLM explanation
- `GET /api/v1/github/{owner}/{repo}/pulls/{number}/review` — review changed Python files in a PR
- `GET /health` — health check

## Security
Never commit `.env` files or API tokens. Copy `.env.example` to your local environment and keep secrets outside Git.

## Project structure
- `app/analyzer.py` — static analysis engine
- `app/github_review.py` — GitHub PR adapter
- `app/llm.py` — optional LLM explanation layer
- `app/models.py` — API schemas
- `static/index.html` — web dashboard
- `tests/` — regression tests
- `.github/workflows/ci.yml` — CI pipeline

## Next production upgrades
Persistent review history, GitHub App webhooks, inline PR comments, organization policies, multi-language parsers, authentication/RBAC, and deployment observability.