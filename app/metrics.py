from prometheus_client import Counter, Histogram, generate_latest

REVIEWS_TOTAL = Counter("code_reviews_total", "Total code reviews", ["language"])
REVIEW_FINDINGS = Counter("code_review_findings_total", "Total findings", ["severity"])
REVIEW_DURATION = Histogram("code_review_duration_seconds", "Review duration")


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), "text/plain; version=0.0.4; charset=utf-8"
