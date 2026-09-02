# AI Code Review & Bug Detection Platform

An API-first static analysis platform that reviews Python source code for bugs, security risks, code smells, and maintainability issues.

## Highlights
- Python AST-based analysis
- Security checks for `eval`, `exec`, shell execution, hard-coded secrets, and unsafe deserialization
- Complexity and long-function heuristics
- Structured findings with severity, line, category, explanation, and remediation
- FastAPI REST API with OpenAPI docs
- No API key required for the core analyzer
- Tests and Docker support

## Architecture
```text
Client -> FastAPI -> Review Service -> AST Analyzer -> Findings
                              |-> Complexity Analyzer
                              |-> Security Rules
```

## Run
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs`.

## API
`POST /api/v1/review`
```json
{"language":"python","code":"def divide(a, b):\n    return a / b"}
```

## Structure
- `app/analyzer.py` — AST analysis engine
- `app/rules.py` — security and quality rules
- `app/models.py` — API schemas
- `tests/` — regression tests

## Roadmap
Repository ingestion, GitHub pull-request comments, JavaScript/TypeScript parsers, LLM-assisted explanations, persistent review history, and organization-level policy configuration.