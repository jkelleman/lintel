"""Runs the ladder over a set of traces and summarizes the result."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .contracts import check_contracts, load_contracts
from .judge import get_judge, judge_trace, load_rubrics, prompt_fingerprint
from .lint import lint_text, load_styleguide
from .models import LAYERS, CaseResult, load_cases, load_traces
from .trajectory import check_trajectory


@dataclass
class Run:
    system: str
    judge: str
    results: list[CaseResult]
    verdicts: dict[str, dict[str, str]] = field(default_factory=dict)  # case_id -> criterion -> verdict
    meta: dict[str, Any] = field(default_factory=dict)

    def by_id(self) -> dict[str, CaseResult]:
        return {r.case.id: r for r in self.results}

    def keyed_verdicts(self) -> dict[str, dict[str, str]]:
        return {f"{self.system}/{cid}": v for cid, v in self.verdicts.items()}


def load_config(path: str | Path = "lintel.yaml") -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def evaluate(traces_path: str | Path, cfg: dict[str, Any], judge_kind: str = "heuristic",
             layers: tuple[str, ...] = LAYERS) -> Run:
    p = cfg["paths"]
    cases = load_cases(p["dataset"])
    traces = load_traces(traces_path)
    guide = load_styleguide(p["styleguide"])
    contracts = load_contracts(p["contracts"])
    rubrics = load_rubrics(p["rubrics"])
    judge = get_judge(judge_kind)

    results, verdicts = [], {}
    for tr in traces:
        case = cases[tr.case_id]
        fs = []
        if "lint" in layers:
            for i, t in tr.assistant_turns():
                fs += lint_text(t.get("content") or "", guide, case.locale, turn=i)
        if "contract" in layers:
            fs += check_contracts(case, tr, contracts)
        if "trajectory" in layers:
            fs += check_trajectory(case, tr)
        if "judge" in layers:
            jf, verdicts[case.id] = judge_trace(judge, case, tr, rubrics)
            fs += jf
        results.append(CaseResult(case, tr, fs))

    meta = {"judge": judge.name, "judge_prompt": prompt_fingerprint(),
            "rubrics": {r["id"]: r["version"] for r in rubrics}, "cases": len(results)}
    if hasattr(judge, "parse_failures"):
        meta["judge_parse_failures"] = judge.parse_failures
    system = traces[0].system if traces else "unknown"
    return Run(system, judge.name, results, verdicts, meta)


def summarize(run: Run) -> dict[str, Any]:
    n = len(run.results)
    passed = sum(r.passed for r in run.results)
    layer_fail = defaultdict(int)
    sev = defaultdict(int)
    for r in run.results:
        for f in r.failures:
            layer_fail[f.layer] += 1
            sev[f.severity] += 1
    tags = defaultdict(lambda: [0, 0])
    for r in run.results:
        for t in r.case.tags + [f"risk:{r.case.risk}", f"locale:{r.case.locale}"]:
            tags[t][0] += r.passed
            tags[t][1] += 1
    return {
        "cases": n, "passed": passed, "pass_rate": round(passed / n, 3) if n else 0.0,
        "failures_by_layer": {layer: layer_fail.get(layer, 0) for layer in LAYERS},
        "failures_by_severity": dict(sev),
        "by_tag": {t: {"passed": a, "total": b, "rate": round(a / b, 2)} for t, (a, b) in sorted(tags.items())},
    }


def gate(run: Run, cfg: dict[str, Any], baseline: Run | None = None) -> tuple[bool, list[str]]:
    """Ship/no-ship. Averages hide regressions, so high-risk cases are gated one by one."""
    g = cfg["gate"]
    s = summarize(run)
    reasons = []
    if s["pass_rate"] < g["min_pass_rate"]:
        reasons.append(f'pass rate {s["pass_rate"]:.0%} is below {g["min_pass_rate"]:.0%}')
    blockers = s["failures_by_severity"].get("blocker", 0)
    if blockers > g["max_blockers"]:
        reasons.append(f"{blockers} blocker finding(s); limit is {g['max_blockers']}")
    if baseline and g.get("no_high_risk_regressions"):
        base = baseline.by_id()
        for r in run.results:
            b = base.get(r.case.id)
            if r.case.risk == "high" and b and b.passed and not r.passed:
                reasons.append(f"high-risk regression on {r.case.id} ({r.case.title})")
    return not reasons, reasons
