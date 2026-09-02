import os


def explain_findings(code: str, findings: list[dict]) -> str:
    """Optional LLM layer. Returns a deterministic fallback when no key is configured."""
    if not findings:
        return "The code passed the configured static checks."
    if not os.getenv("OPENAI_API_KEY"):
        return "Static analysis found issues. Configure OPENAI_API_KEY to generate an AI explanation and fix plan."

    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    prompt = (
        "You are a senior code reviewer. Explain the following static-analysis findings "
        "concisely, prioritize the highest-risk issue, and give a safe fix plan.\n\n"
        f"Findings: {findings}\n\nCode:\n{code}"
    )
    response = client.responses.create(model=model, input=prompt)
    return response.output_text
