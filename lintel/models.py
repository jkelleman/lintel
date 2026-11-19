"""Core data shapes. Everything in lintel is a Finding attached to a case."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Severity is a product decision. Content design owns it.
SEVERITY_ORDER = {"blocker": 3, "major": 2, "minor": 1, "info": 0}

# The four rungs of the eval ladder, cheapest and most deterministic first.
LAYERS = ("lint", "contract", "trajectory", "judge")


@dataclass
class Finding:
    layer: str            # one of LAYERS
    check: str            # rule or criterion id, e.g. "banned.simply"
    severity: str         # blocker | major | minor | info
    passed: bool
    message: str          # written for a content designer
    evidence: str = ""    # the exact text that triggered it
    turn: int | None = None
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Case:
    id: str
    title: str
    tags: list[str]
    locale: str = "en"
    risk: str = "low"
    context: dict[str, Any] = field(default_factory=dict)
    expect: dict[str, Any] = field(default_factory=dict)


@dataclass
class Trace:
    case_id: str
    system: str
    turns: list[dict[str, Any]]

    def assistant_turns(self) -> list[tuple[int, dict[str, Any]]]:
        return [(i, t) for i, t in enumerate(self.turns) if t["role"] == "assistant"]

    def final_reply(self) -> str:
        for t in reversed(self.turns):
            if t["role"] == "assistant" and t.get("content"):
                return t["content"]
        return ""

    def last_user_request(self) -> str:
        for t in reversed(self.turns):
            if t["role"] == "user":
                return t["content"]
        return ""


@dataclass
class CaseResult:
    case: Case
    trace: Trace
    findings: list[Finding]

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if not f.passed]

    @property
    def worst(self) -> str:
        fails = self.failures
        if not fails:
            return "pass"
        return max(fails, key=lambda f: SEVERITY_ORDER[f.severity]).severity

    @property
    def passed(self) -> bool:
        # A case fails on any blocker or major. Minors are reported and don't gate.
        return self.worst in ("pass", "minor", "info")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("//"):
            rows.append(json.loads(line))
    return rows


def load_cases(path: str | Path) -> dict[str, Case]:
    return {r["id"]: Case(**r) for r in read_jsonl(path)}


def load_traces(path: str | Path) -> list[Trace]:
    return [Trace(**r) for r in read_jsonl(path)]
