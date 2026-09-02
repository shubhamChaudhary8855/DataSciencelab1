import ast
import re
from dataclasses import dataclass


@dataclass
class RawFinding:
    rule_id: str
    severity: str
    category: str
    line: int
    message: str
    remediation: str


SECRET_RE = re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{6,}['\"]")


def _finding(rule_id, severity, category, node, message, remediation):
    return RawFinding(rule_id, severity, category, getattr(node, "lineno", 1), message, remediation)


def analyze_python(code: str) -> list[RawFinding]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [RawFinding("PY-SYNTAX", "critical", "correctness", exc.lineno or 1,
                            f"Syntax error: {exc.msg}", "Fix the syntax error before running the code.")]

    findings: list[RawFinding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "eval":
                findings.append(_finding("SEC-EVAL", "high", "security", node,
                    "Dynamic eval() can execute attacker-controlled code.", "Avoid eval(); parse and validate allowed input explicitly."))
            elif node.func.id == "exec":
                findings.append(_finding("SEC-EXEC", "critical", "security", node,
                    "exec() executes arbitrary Python code at runtime.", "Remove exec() or replace it with a constrained operation."))
            elif node.func.id in {"pickle", "loads"}:
                findings.append(_finding("SEC-DESER", "high", "security", node,
                    "Unsafe deserialization can execute malicious payloads.", "Use a safe, schema-validated serialization format such as JSON."))
            elif node.func.id == "system":
                findings.append(_finding("SEC-SHELL", "high", "security", node,
                    "Shell execution can become command injection when input is untrusted.", "Prefer subprocess with a list of arguments and shell=False."))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        findings.append(_finding("SEC-SHELL", "high", "security", node,
                            "subprocess(..., shell=True) can enable command injection.", "Use shell=False and pass arguments as a list."))

        if isinstance(node, ast.FunctionDef):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > 60:
                findings.append(_finding("QUAL-LONG-FUNC", "medium", "maintainability", node,
                    f"Function spans {length} lines and is difficult to maintain.", "Split the function into focused, testable helpers."))

        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append(_finding("QUAL-BARE-EXCEPT", "medium", "correctness", node,
                "Bare except catches every exception, including system-exiting exceptions.", "Catch the narrowest expected exception type."))

    for line_no, line in enumerate(code.splitlines(), 1):
        if SECRET_RE.search(line):
            findings.append(RawFinding("SEC-HARDCODED-SECRET", "critical", "security", line_no,
                "A possible credential or secret is hard-coded in source code.", "Move secrets to environment variables or a secret manager."))
        if len(line) > 120:
            findings.append(RawFinding("QUAL-LONG-LINE", "low", "maintainability", line_no,
                "Line exceeds 120 characters.", "Break the expression into smaller, readable statements."))

    return findings


def review(code: str, language: str) -> tuple[int, list[RawFinding]]:
    if language.lower() != "python":
        return 0, [RawFinding("LANG-UNSUPPORTED", "low", "configuration", 1,
            f"Language '{language}' is not supported yet.", "Use Python or add a parser for this language.")]
    findings = analyze_python(code)
    penalties = {"critical": 30, "high": 18, "medium": 8, "low": 2}
    score = max(0, 100 - sum(penalties.get(f.severity, 0) for f in findings))
    return score, findings
