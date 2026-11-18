"""Reports written for the people who own the words: content designers and PMs.

Every finding reads as a sentence with evidence and a fix, not a stack trace.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .models import LAYERS, SEVERITY_ORDER
from .runner import Run, summarize

LAYER_NAMES = {"lint": "1 · Lint", "contract": "2 · Contracts", "trajectory": "3 · Trajectory", "judge": "4 · Judge"}


def compare(base: Run, cand: Run) -> list[dict[str, Any]]:
    b = base.by_id()
    rows = []
    for r in cand.results:
        o = b.get(r.case.id)
        if not o:
            continue
        old = {f.check for f in o.failures if f.severity in ("blocker", "major")}
        new = {f.check for f in r.failures if f.severity in ("blocker", "major")}
        change = ("regressed" if o.passed and not r.passed else
                  "fixed" if not o.passed and r.passed else
                  "still failing" if not r.passed else "still passing")
        rows.append({"case_id": r.case.id, "title": r.case.title, "risk": r.case.risk, "change": change,
                     "new_failures": sorted(new - old), "fixed_failures": sorted(old - new)})
    order = {"regressed": 0, "still failing": 1, "fixed": 2, "still passing": 3}
    return sorted(rows, key=lambda x: (order[x["change"]], x["case_id"]))


# ---------------------------------------------------------------- markdown

def to_markdown(run: Run, verdict: tuple[bool, list[str]], diff: list[dict] | None = None,
                calib: list[dict] | None = None) -> str:
    s = summarize(run)
    ok, reasons = verdict
    lines = [f"# lintel report · `{run.system}`", "",
             f"**Gate: {'✅ SHIP' if ok else '⛔ HOLD'}**" + ("" if ok else " — " + "; ".join(reasons)), "",
             f"{s['passed']}/{s['cases']} cases pass ({s['pass_rate']:.0%}). Judge: `{run.meta['judge']}`, "
             f"prompt `{run.meta['judge_prompt']}`, rubrics {run.meta['rubrics']}.", "",
             "| Rung | Failures |", "|---|---|"]
    lines += [f"| {LAYER_NAMES[layer]} | {s['failures_by_layer'][layer]} |" for layer in LAYERS]
    if diff:
        lines += ["", "## Baseline → candidate", "", "| Case | Risk | Change | New failures | Fixed |", "|---|---|---|---|---|"]
        lines += [f"| {d['case_id']} {d['title']} | {d['risk']} | **{d['change']}** | {', '.join(d['new_failures']) or '—'} "
                  f"| {', '.join(d['fixed_failures']) or '—'} |" for d in diff]
    if calib:
        lines += ["", "## Judge calibration (vs human labels)", "", "| Criterion | n | Agreement | κ | Status |", "|---|---|---|---|---|"]
        lines += [f"| {c['criterion']} | {c['n']} | {c['agreement']:.0%} | {c['kappa']:.2f} | {c['status']} |" for c in calib]
    lines += ["", "## Failing cases", ""]
    for r in run.results:
        if not r.failures:
            continue
        lines.append(f"### {r.case.id} · {r.case.title} — {'pass' if r.passed else 'FAIL'} (worst: {r.worst})")
        for f in sorted(r.failures, key=lambda f: -SEVERITY_ORDER[f.severity]):
            ev = f" — “{f.evidence}”" if f.evidence else ""
            fix = f" → {f.suggestion}" if f.suggestion else ""
            lines.append(f"- `{f.severity}` **{f.check}** ({f.layer}): {f.message}{ev}{fix}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- html

CSS = """
:root{--ink:#1d2321;--muted:#5d6763;--line:#dfe3e1;--bg:#f7f6f2;--card:#fff;--ok:#1f7a4d;--warn:#a15c07;--bad:#b42318;--accent:#0b5c78}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg)}
main{max-width:1040px;margin:0 auto;padding:40px 24px 80px}h1{font-size:28px;margin:0 0 4px;letter-spacing:-.01em}h2{font-size:18px;margin:40px 0 12px}
.sub{color:var(--muted);margin:0 0 24px}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}
.gate{display:flex;gap:16px;align-items:center;padding:18px 20px;border-radius:10px;background:var(--card);border:1px solid var(--line);border-left:6px solid var(--ok)}
.gate.hold{border-left-color:var(--bad)}.gate b{font-size:20px}.gate ul{margin:4px 0 0;padding-left:18px;color:var(--muted)}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:16px}.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.tile .n{font-size:26px;font-weight:650;font-variant-numeric:tabular-nums}.tile .l{color:var(--muted);font-size:13px}
.ladder{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}.rung{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.rung .n{font-size:22px;font-weight:650}.rung small{display:block;color:var(--muted)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14px}th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);background:#fbfbf9}
.pill{display:inline-block;padding:1px 8px;border-radius:99px;font-size:12px;font-weight:600;white-space:nowrap}
.blocker,.regressed,.nt{background:#fde7e5;color:var(--bad)}.major,.sf{background:#fdf0dc;color:var(--warn)}.minor{background:#eef1f0;color:var(--muted)}
.fixed,.pass,.tr{background:#e3f3ea;color:var(--ok)}.sp{background:#eef1f0;color:var(--muted)}.us{background:#e5f0f5;color:var(--accent)}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0;padding:0}summary{cursor:pointer;padding:12px 16px;display:flex;gap:10px;align-items:center}
details[open] summary{border-bottom:1px solid var(--line)}.case-body{padding:12px 16px}.f{padding:8px 0;border-bottom:1px dashed var(--line)}.f:last-child{border:0}
.ev{color:var(--muted)}.fix{color:var(--accent)}.turn{white-space:pre-wrap;background:#fbfbf9;border:1px solid var(--line);border-radius:6px;padding:8px 10px;margin:6px 0;font-size:13.5px}
.role{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
@media(max-width:700px){.tiles,.ladder{grid-template-columns:repeat(2,1fr)}}
"""


def _e(x: Any) -> str:
    return html.escape(str(x))


def _cls(change: str) -> str:
    return {"regressed": "regressed", "fixed": "fixed", "still failing": "sf", "still passing": "sp"}[change]


def to_html(run: Run, verdict: tuple[bool, list[str]], diff: list[dict] | None = None,
            calib: list[dict] | None = None, base: Run | None = None) -> str:
    s = summarize(run)
    ok, reasons = verdict
    out = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>lintel · {_e(run.system)}</title><style>{CSS}</style></head><body><main>",
           f"<h1>lintel report · {_e(run.system)}</h1>",
           f"<p class='sub'>Judge <span class='mono'>{_e(run.meta['judge'])}</span> · prompt "
           f"<span class='mono'>{_e(run.meta['judge_prompt'])}</span> · rubrics "
           f"<span class='mono'>{_e(json.dumps(run.meta['rubrics']))}</span></p>",
           f"<div class='gate {'' if ok else 'hold'}'><b>{'Ship' if ok else 'Hold'}</b><div>"
           + ("All release gates pass." if ok else "<ul>" + "".join(f"<li>{_e(r)}</li>" for r in reasons) + "</ul>")
           + "</div></div>"]
    sev = s["failures_by_severity"]
    regress = sum(d["change"] == "regressed" for d in diff or [])
    tiles = [(f"{s['pass_rate']:.0%}", f"{s['passed']} of {s['cases']} cases pass"),
             (sev.get("blocker", 0), "blocker findings"), (sev.get("major", 0), "major findings"),
             (regress if diff else "—", "regressions vs baseline" if diff else "no baseline compared")]
    out.append("<div class='tiles'>" + "".join(f"<div class='tile'><div class='n'>{_e(n)}</div><div class='l'>{_e(l)}</div></div>"
                                              for n, l in tiles) + "</div>")
    blurbs = {"lint": "word lists, length, reading level", "contract": "reply shape per situation",
              "trajectory": "what the agent did", "judge": "rubric, one criterion per call"}
    out.append("<h2>Where failures were caught</h2><div class='ladder'>" + "".join(
        f"<div class='rung'><small>{LAYER_NAMES[layer]}</small><div class='n'>{s['failures_by_layer'][layer]}</div><small>{blurbs[layer]}</small></div>"
        for layer in LAYERS) + "</div>")

    if diff:
        out.append(f"<h2>Baseline → candidate</h2><table><tr><th>Case</th><th>Risk</th><th>Change</th><th>New failures</th><th>Fixed</th></tr>")
        for d in diff:
            out.append(f"<tr><td><b>{_e(d['case_id'])}</b> {_e(d['title'])}</td><td>{_e(d['risk'])}</td>"
                       f"<td><span class='pill {_cls(d['change'])}'>{_e(d['change'])}</span></td>"
                       f"<td class='mono'>{_e(', '.join(d['new_failures']) or '—')}</td><td class='mono'>{_e(', '.join(d['fixed_failures']) or '—')}</td></tr>")
        out.append("</table>")

    if calib:
        out.append("<h2>Can we trust the judge?</h2><p class='sub'>Judge verdicts vs. human labels, per criterion. "
                   "Cohen's κ corrects for agreement by chance. Below 0.60, fix the rubric before gating on it.</p>"
                   "<table><tr><th>Criterion</th><th>n</th><th>Agreement</th><th>κ</th><th>Status</th><th>Disagreements</th></tr>")
        cmap = {"trusted": "tr", "usable": "us", "not trusted": "nt"}
        for c in calib:
            dis = "<br>".join(f"<b>{_e(d['case_id'])}</b>: human <i>{_e(d['human'])}</i>, judge <i>{_e(d['judge'])}</i>"
                              + (f" <span class='ev'>· {_e(d['note'])}</span>" if d["note"] else "") for d in c["disagreements"]) or "—"
            out.append(f"<tr><td class='mono'>{_e(c['criterion'])}</td><td>{c['n']}</td><td>{c['agreement']:.0%}</td>"
                       f"<td><b>{c['kappa']:.2f}</b></td><td><span class='pill {cmap[c['status']]}'>{_e(c['status'])}</span></td><td>{dis}</td></tr>")
        out.append("</table>")

    out.append("<h2>Cases</h2>")
    for r in sorted(run.results, key=lambda r: (r.passed, r.case.id)):
        badge = f"<span class='pill {'pass' if r.passed else r.worst}'>{'pass' if r.passed else r.worst}</span>"
        out.append(f"<details{'' if r.passed else ' open'}><summary>{badge}<b>{_e(r.case.id)}</b> {_e(r.case.title)}"
                   f"<span class='ev'>· {', '.join(_e(t) for t in r.case.tags)}</span></summary><div class='case-body'>")
        for f in sorted(r.failures, key=lambda f: -SEVERITY_ORDER[f.severity]):
            out.append(f"<div class='f'><span class='pill {f.severity}'>{f.severity}</span> <span class='mono'>{_e(f.check)}</span> "
                       f"<span class='ev'>({LAYER_NAMES[f.layer]})</span><br>{_e(f.message)}"
                       + (f"<br><span class='ev'>Evidence: “{_e(f.evidence)}”</span>" if f.evidence else "")
                       + (f"<br><span class='fix'>Fix: {_e(f.suggestion)}</span>" if f.suggestion else "") + "</div>")
        if not r.failures:
            out.append("<div class='ev'>No findings.</div>")
        out.append("<details style='margin-top:10px'><summary>Transcript</summary><div class='case-body'>")
        for t in r.trace.turns:
            body = t.get("content") if t["role"] != "tool" else f"{t.get('name')} · {t.get('status', 'ok')} · {json.dumps(t.get('content'))}"
            calls = "".join(f"\n→ calls {c['name']}({json.dumps(c.get('args', {}))})" for c in t.get("tool_calls", []) or [])
            out.append(f"<div class='role'>{_e(t['role'])}</div><div class='turn'>{_e(body)}{_e(calls)}</div>")
        out.append("</div></details></div></details>")
    out.append("<p class='sub' style='margin-top:40px'>Generated by lintel. Sample data is fictional.</p></main></body></html>")
    return "".join(out)


def write_reports(outdir: str | Path, name: str, md: str, page: str, data: dict) -> list[Path]:
    d = Path(outdir)
    d.mkdir(parents=True, exist_ok=True)
    paths = [d / f"{name}.md", d / f"{name}.html", d / f"{name}.json"]
    paths[0].write_text(md, encoding="utf-8")
    paths[1].write_text(page, encoding="utf-8")
    paths[2].write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return paths
