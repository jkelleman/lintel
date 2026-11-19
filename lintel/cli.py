"""lintel command line.

  python -m lintel lint "Simply click on Export."           # rung 1 on any string
  python -m lintel run runs/candidate.jsonl --baseline runs/baseline.jsonl
  python -m lintel calibrate runs/candidate.jsonl           # judge vs. humans
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .calibrate import calibrate
from .lint import lint_text, load_styleguide
from .models import LAYERS
from .report import compare, to_html, to_markdown, write_reports
from .runner import evaluate, gate, load_config, summarize


def _print_findings(fs) -> None:
    if not fs:
        print("✓ no findings")
    for f in fs:
        ev = f': "{f.evidence}"' if f.evidence else ""
        print(f"  {f.severity:<7} {f.check}{ev}\n          {f.message}" + (f"\n          fix: {f.suggestion}" if f.suggestion else ""))


def cmd_lint(a, cfg) -> int:
    text = Path(a.text).read_text(encoding="utf-8") if Path(a.text).is_file() else a.text
    fs = lint_text(text, load_styleguide(cfg["paths"]["styleguide"]), a.locale)
    _print_findings(fs)
    return 1 if any(f.severity in ("blocker", "major") for f in fs) else 0


def cmd_run(a, cfg) -> int:
    layers = tuple(a.layers.split(",")) if a.layers else LAYERS
    run = evaluate(a.traces, cfg, a.judge, layers)
    base = evaluate(a.baseline, cfg, a.judge, layers) if a.baseline else None
    diff = compare(base, run) if base else None
    calib = None
    if a.labels and Path(a.labels).is_file() and "judge" in layers:
        keyed = {**(base.keyed_verdicts() if base else {}), **run.keyed_verdicts()}
        calib = calibrate(keyed, a.labels)
    verdict = gate(run, cfg, base)

    s = summarize(run)
    ok, reasons = verdict
    print(f"\nlintel · {run.system} · judge={run.meta['judge']}")
    print(f"  {s['passed']}/{s['cases']} cases pass ({s['pass_rate']:.0%})")
    print("  failures by level: " + "  ".join(f"{k}={v}" for k, v in s["failures_by_layer"].items()))
    if diff:
        for d in diff:
            if d["change"] in ("regressed", "fixed"):
                print(f"  {d['change']:<9} {d['case_id']} {d['title']}")
    if calib:
        for c in calib:
            print(f"  judge κ {c['kappa']:>5.2f}  {c['status']:<11} {c['criterion']}")
    print(f"\n  GATE: {'SHIP' if ok else 'HOLD'}" + ("" if ok else "\n   - " + "\n   - ".join(reasons)))

    name = a.name or run.system
    data = {"summary": s, "meta": run.meta, "gate": {"ship": ok, "reasons": reasons}, "diff": diff, "calibration": calib,
            "cases": [{"id": r.case.id, "passed": r.passed, "worst": r.worst,
                       "findings": [f.to_dict() for f in r.findings]} for r in run.results]}
    paths = write_reports(a.out, name, to_markdown(run, verdict, diff, calib), to_html(run, verdict, diff, calib, base), data)
    print("  reports: " + ", ".join(str(p) for p in paths))
    return 0 if ok or a.no_gate else 1


def cmd_calibrate(a, cfg) -> int:
    keyed = {}
    for path in a.traces:
        keyed.update(evaluate(path, cfg, a.judge, ("judge",)).keyed_verdicts())
    report = calibrate(keyed, a.labels)
    for c in report:
        print(f"{c['criterion']:<34} n={c['n']:<3} agree={c['agreement']:.0%}  κ={c['kappa']:.2f}  {c['status']}")
        for d in c["disagreements"]:
            print(f"    {d['case_id']}: human={d['human']} judge={d['judge']}  {d['note']}")
    if a.json:
        print(json.dumps(report, indent=2))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="lintel", description="From prose linter to agent evals.")
    p.add_argument("--config", default="lintel.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    l = sub.add_parser("lint", help="Run the style guide on a string or file")
    l.add_argument("text")
    l.add_argument("--locale", default="en")

    r = sub.add_parser("run", help="Run the full ladder on a trace file")
    r.add_argument("traces")
    r.add_argument("--baseline")
    r.add_argument("--judge", choices=["heuristic", "claude"], default="heuristic")
    r.add_argument("--labels", default="labels/human_labels.jsonl")
    r.add_argument("--layers", help="comma list, e.g. lint,contract")
    r.add_argument("--out", default="reports")
    r.add_argument("--name")
    r.add_argument("--no-gate", action="store_true", help="always exit 0")

    c = sub.add_parser("calibrate", help="Check judge agreement with human labels")
    c.add_argument("traces", nargs="+")
    c.add_argument("--labels", default="labels/human_labels.jsonl")
    c.add_argument("--judge", choices=["heuristic", "claude"], default="heuristic")
    c.add_argument("--json", action="store_true")

    a = p.parse_args(argv)
    cfg = load_config(a.config)
    return {"lint": cmd_lint, "run": cmd_run, "calibrate": cmd_calibrate}[a.cmd](a, cfg)


if __name__ == "__main__":
    sys.exit(main())
