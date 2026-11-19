"""Reports written for the people who own the words: content designers and PMs.

Every finding reads as a sentence with evidence and a suggested fix.
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
    lines = [f"# lintel report: {run.system}", "",
             f"**Gate: {'✅ SHIP' if ok else '⛔ HOLD'}**" + ("" if ok else ": " + " ".join(reasons)), "",
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
    lines += ["", "## Cases with findings", ""]
    for r in run.results:
        if not r.failures:
            continue
        lines.append(f"### {r.case.id} · {r.case.title} · {'pass' if r.passed else 'FAIL'} (worst: {r.worst})")
        for f in sorted(r.failures, key=lambda f: -SEVERITY_ORDER[f.severity]):
            ev = f": “{f.evidence}”" if f.evidence else ""
            fix = f" → {f.suggestion}" if f.suggestion else ""
            lines.append(f"- `{f.severity}` **{f.check}** ({f.layer}): {f.message}{ev}{fix}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- html

CSS = """
:root{--mint:#DFF3E8;--mint2:#EEF8F2;--ink:#2B2A4C;--soft:#5E5D82;--line:#D5E6DC;--violet:#6B5BD2;
--hi:#FFE36E;--pen:#E0457B;--leaf:#2F9E6A;--amber:#B7791F;--paper:#fff}
*{box-sizing:border-box}
body{margin:0;background:var(--mint);color:var(--ink);font:17px/1.55 Nunito,ui-rounded,"SF Pro Rounded",system-ui,sans-serif}
main{max-width:920px;margin:0 auto;padding:48px 24px 96px}
h1{font-size:40px;font-weight:900;letter-spacing:-.8px;line-height:1.1;margin:0 0 8px}
h2{font-size:24px;font-weight:800;margin:56px 0 6px;letter-spacing:-.2px}
.lede{color:var(--soft);margin:0 0 28px;max-width:62ch}
.hand{font-family:Kalam,"Bradley Hand","Segoe Print",cursive;font-weight:700;color:var(--pen)}
code{font:600 .82em ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--mint2);border-radius:6px;padding:1px 6px;color:var(--ink)}
.verdict{background:var(--paper);border-radius:28px 28px 28px 8px;padding:22px 28px;max-width:640px}
.verdict .hand{font-size:34px;line-height:1.1;display:block;margin-bottom:6px}
.verdict.ship .hand{color:var(--leaf)}
.verdict ul{margin:6px 0 0;padding-left:20px}
.summary{font-size:22px;font-weight:700;margin:28px 0 0;max-width:62ch}
.summary b{background:linear-gradient(transparent 55%,var(--hi) 55%);font-weight:800}
.ladder{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-top:14px}
.ladder strong{display:block;font-size:30px;font-weight:900;line-height:1.1}
.ladder span{color:var(--soft);font-size:15px}
table{width:100%;border-collapse:collapse;background:var(--paper);border-radius:20px;overflow:hidden;margin-top:14px}
th,td{text-align:left;padding:12px 16px;border-bottom:1px solid var(--line);vertical-align:top;font-size:15.5px}
th{font-weight:800;color:var(--soft);font-size:14.5px}
tr:last-child td{border-bottom:0}
td:first-child{min-width:190px}
.pill{display:inline-block;padding:2px 12px;border-radius:99px;font-size:13.5px;font-weight:800;white-space:nowrap}
.blocker,.regressed,.nt{background:#FBE1EA;color:#B3255A}.major,.sf{background:#FCEFD3;color:#8A5A12}
.minor,.sp{background:var(--mint2);color:var(--soft)}.fixed,.pass,.tr{background:#DDF2E6;color:#1F7A50}.us{background:#E9E5FA;color:#4E3FB0}
details.case{background:var(--paper);border-radius:22px;margin:12px 0}
details.case>summary{cursor:pointer;padding:16px 22px;display:flex;gap:12px;align-items:center;font-weight:800;list-style:none}
details.case>summary::-webkit-details-marker{display:none}
details.case>summary:focus-visible{outline:3px solid var(--violet);outline-offset:2px;border-radius:22px}
.case-body{padding:0 22px 20px}
.tags{color:var(--soft);font-weight:600;font-size:14.5px;margin-left:auto}
.f{padding:12px 0;border-top:1px solid var(--line)}
.f p{margin:4px 0 0}.ev{color:var(--soft)}
.f .hand{font-size:21px;display:block;margin-top:4px;line-height:1.25}
.chat{background:var(--mint2);border-radius:18px;padding:16px;margin-top:14px;display:flex;flex-direction:column;gap:10px}
.msg{max-width:78%;padding:10px 16px;border-radius:20px;font-size:15.5px;white-space:pre-wrap}
.msg.user{align-self:flex-end;background:var(--violet);color:#fff;border-bottom-right-radius:6px}
.msg.assistant{align-self:flex-start;background:var(--paper);border-bottom-left-radius:6px}
.msg.tool{align-self:center;max-width:92%;background:transparent;color:var(--soft);font-size:13.5px;padding:2px 8px;text-align:center}
.calls{display:block;color:var(--soft);font-size:13.5px;margin-top:4px}
.foot{color:var(--soft);font-size:14.5px;margin-top:56px}
@media(max-width:640px){h1{font-size:32px}.ladder{grid-template-columns:repeat(2,1fr)}.msg{max-width:92%}.tags{display:none}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""


def _e(x: Any) -> str:
    return html.escape(str(x))


def _cls(change: str) -> str:
    return {"regressed": "regressed", "fixed": "fixed", "still failing": "sf", "still passing": "sp"}[change]


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def to_html(run: Run, verdict: tuple[bool, list[str]], diff: list[dict] | None = None,
            calib: list[dict] | None = None, base: Run | None = None) -> str:
    s = summarize(run)
    ok, reasons = verdict
    sev = s["failures_by_severity"]
    regress = sum(d["change"] == "regressed" for d in diff or [])
    rubrics = ", ".join(f"{k} v{v}" for k, v in run.meta["rubrics"].items())
    out = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>lintel report: {_e(run.system)}</title><style>{CSS}</style></head><body><main>",
           f"<h1>How did the {_e(run.system)} do?</h1>",
           f"<p class='lede'>Scored with the {_e(run.meta['judge'])} judge, prompt version {_e(run.meta['judge_prompt'])}, "
           f"and rubrics {_e(rubrics)}.</p>",
           f"<div class='verdict {'ship' if ok else 'hold'}'><span class='hand'>{'Ready to ship.' if ok else 'Hold for now.'}</span>"
           + ("Every release check passed." if ok else "<ul>" + "".join(f"<li>{_e(r)}</li>" for r in reasons) + "</ul>")
           + "</div>"]
    parts = [f"<b>{s['passed']} of {s['cases']}</b> cases pass", f"{_plural(sev.get('blocker', 0), 'blocker')}",
             f"{_plural(sev.get('major', 0), 'major finding')}"]
    if diff:
        parts.append(f"<b>{_plural(regress, 'regression')}</b> since the baseline")
    out.append("<p class='summary'>" + ", ".join(parts[:-1]) + ", and " + parts[-1] + ".</p>")

    blurbs = {"lint": "word choice and reading level", "contract": "reply shape for the situation",
              "trajectory": "what the agent did", "judge": "rubric scores"}
    out.append("<h2>Where problems were caught</h2><p class='lede'>Cheaper checks run first. Each count is the number of findings at that level.</p><div class='ladder'>"
               + "".join(f"<div><strong>{s['failures_by_layer'][layer]}</strong><span>{LAYER_NAMES[layer].split(' · ')[1]}: {blurbs[layer]}</span></div>"
                         for layer in LAYERS) + "</div>")

    if diff:
        out.append("<h2>What changed since the baseline</h2><table><tr><th>Case</th><th>Risk</th><th>Change</th><th>New problems</th><th>Fixed</th></tr>")
        for d in diff:
            nf = " ".join(f"<code>{_e(x)}</code>" for x in d["new_failures"]) or "None"
            fx = " ".join(f"<code>{_e(x)}</code>" for x in d["fixed_failures"]) or "None"
            out.append(f"<tr><td><b>{_e(d['case_id'])}</b> {_e(d['title'])}</td><td>{_e(d['risk'])}</td>"
                       f"<td><span class='pill {_cls(d['change'])}'>{_e(d['change'])}</span></td><td>{nf}</td><td>{fx}</td></tr>")
        out.append("</table>")

    if calib:
        out.append("<h2>Can we trust the judge?</h2><p class='lede'>The judge's verdicts compared with human labels. "
                   "Cohen's κ corrects for agreement by chance. Below 0.60, fix the rubric before using that criterion to gate a release.</p>"
                   "<table><tr><th>Criterion</th><th>Agreement</th><th>κ</th><th>Status</th><th>Where they disagreed</th></tr>")
        cmap = {"trusted": "tr", "usable": "us", "not trusted": "nt"}
        for c in calib:
            dis = "<br><br>".join(f"<b>{_e(d['case_id'])}</b>: people said {_e(d['human'])}, the judge said {_e(d['judge'])}."
                                  + (f" <span class='ev'>{_e(d['note'])}</span>" if d["note"] else "") for d in c["disagreements"]) or "None"
            out.append(f"<tr><td><code>{_e(c['criterion'])}</code><br><span class='ev'>{c['n']} labels</span></td><td>{c['agreement']:.0%}</td>"
                       f"<td><b>{c['kappa']:.2f}</b></td><td><span class='pill {cmap[c['status']]}'>{_e(c['status'])}</span></td><td>{dis}</td></tr>")
        out.append("</table>")

    out.append("<h2>Every case</h2><p class='lede'>Cases with problems are open. Each one shows the conversation the finding came from.</p>")
    for r in sorted(run.results, key=lambda r: (r.passed, r.case.id)):
        badge = f"<span class='pill {'pass' if r.passed else r.worst}'>{'pass' if r.passed else r.worst}</span>"
        out.append(f"<details class='case'{'' if r.passed else ' open'}><summary>{badge}<span>{_e(r.case.id)} {_e(r.case.title)}</span>"
                   f"<span class='tags'>{_e(', '.join(r.case.tags))}</span></summary><div class='case-body'>")
        said = " ".join(t.get("content") or "" for t in r.trace.turns if t["role"] == "assistant")
        for f in sorted(r.failures, key=lambda f: -SEVERITY_ORDER[f.severity]):
            out.append(f"<div class='f'><span class='pill {f.severity}'>{f.severity}</span> <code>{_e(f.check)}</code>"
                       f"<p>{_e(f.message)}</p>"
                       + ((f"<p class='ev'>It said: “{_e(f.evidence)}”</p>" if f.evidence in said else f"<p class='ev'>{_e(f.evidence)}</p>") if f.evidence else "")
                       + (f"<span class='hand'>{_e(f.suggestion)}</span>" if f.suggestion else "") + "</div>")
        if not r.failures:
            out.append("<p class='ev'>No problems found.</p>")
        out.append("<div class='chat'>")
        for t in r.trace.turns:
            calls = "".join(f"<span class='calls'>Called {_e(c['name'])}</span>" for c in t.get("tool_calls", []) or [])
            if t["role"] == "tool":
                out.append(f"<div class='msg tool'>{_e(t.get('name'))} returned {_e(t.get('status', 'ok'))}: {_e(json.dumps(t.get('content')))}</div>")
            elif t.get("content") or calls:
                out.append(f"<div class='msg {t['role']}'>{_e(t.get('content') or '')}{calls}</div>")
        out.append("</div></div></details>")
    out.append("<p class='foot'>Made with lintel. The sample data is fictional.</p></main></body></html>")
    return "".join(out)


def write_reports(outdir: str | Path, name: str, md: str, page: str, data: dict) -> list[Path]:
    d = Path(outdir)
    d.mkdir(parents=True, exist_ok=True)
    paths = [d / f"{name}.md", d / f"{name}.html", d / f"{name}.json"]
    paths[0].write_text(md, encoding="utf-8")
    paths[1].write_text(page, encoding="utf-8")
    paths[2].write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return paths
