"""Rung 4: rubric judges.

Two interchangeable judges share one interface:
  * HeuristicJudge — deterministic stand-in so the whole pipeline runs offline,
    in CI, with no API key. Also a useful floor: if an LLM judge can't beat
    the heuristic's agreement with humans, the rubric is the problem.
  * ClaudeJudge — LLM-as-judge with the hygiene that makes it trustworthy:
    one criterion per call, anchored scale, evidence quote required,
    reasoning before verdict, temperature 0, strict JSON, parse failures
    counted rather than silently dropped.

Neither judge is trusted until `lintel calibrate` shows it agrees with humans.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Protocol

import yaml

from .models import Case, Finding, Trace
from .text import fk_grade, numbers, sentences, words

VERDICTS = ("pass", "partial", "fail", "na")


def load_rubrics(folder: str | Path) -> list[dict[str, Any]]:
    return [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(Path(folder).glob("*.yaml"))]


def verdict_to_finding(rubric: dict, crit: dict, verdict: str, evidence: str, reason: str) -> Finding | None:
    if verdict == "na":
        return None
    sev = crit["severity"] if verdict == "fail" else ("minor" if verdict == "partial" else "info")
    return Finding("judge", f'{rubric["id"]}.{crit["id"]}', sev, verdict == "pass",
                   f"[{verdict}] {reason}", evidence=evidence)


class Judge(Protocol):
    name: str

    def grade(self, case: Case, trace: Trace, rubric: dict, crit: dict) -> tuple[str, str, str]:
        """Return (verdict, evidence, reason)."""


# ---------------------------------------------------------------- heuristic judge

_STOP = set("""a an the and or but to of for in on at with by is are was were be this that it its my me i you your
can could would should do does did how what why when where which please all from as into about our we whatever me
el la los las de del que y o en un una para por con mi me cómo qué es son""".split())
_AUTHORITY = ["code official", "authority having jurisdiction", "ahj", "engineer of record",
              "architect of record", "local code", "jurisdiction", "building department"]
_HEDGE = ["may", "might", "check", "verify", "depends", "typically", "usually"]
# An imperative at the start of a sentence, or right after a lead-in clause ("To undo it, select…").
_IMPERATIVE = re.compile(r"(?:^|[:,;]\s+|\bthen\s+)(select|open|go to|try|run|choose|check|reduce|turn|set|use|"
                         r"click|drag|re-run|sign in|selecciona|abre|ve a|elige|cambia|haz)\b", re.I)
_DONE = re.compile(r"^I (\w+ed|set|ran|made|put|found|undid)\b")
_BLAME = ["you failed", "you forgot", "your mistake", "user error"]
_CONDESCEND = ["obviously", "simply", "as you should know", "it's easy", "basic concept", "just"]


def _sources(case: Case, trace: Trace) -> str:
    parts = [t.get("content", "") for t in trace.turns if t["role"] == "user"]
    parts += [json.dumps(t.get("content", "")) for t in trace.turns if t["role"] == "tool"]
    parts += [d.get("text", "") + " " + d.get("title", "") for d in case.context.get("docs", [])]
    return " ".join(str(p) for p in parts)


def _stem(w: str) -> str:
    for suf in ("ing", "es", "ed", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def _content_words(text: str) -> set[str]:
    return {_stem(w.lower()) for w in words(text) if len(w) > 2 and w.lower() not in _STOP}


def _claims_only(reply: str) -> str:
    """Drop questions and examples: "Level 2, for example?" is an offer, not a claim."""
    return " ".join(s for s in sentences(reply) if not s.rstrip().endswith("?") and "for example" not in s.lower())


class HeuristicJudge:
    name = "heuristic-v1"

    def grade(self, case: Case, trace: Trace, rubric: dict, crit: dict) -> tuple[str, str, str]:
        reply = trace.final_reply()
        cid = crit["id"]
        low = reply.lower()

        if cid == "claims_supported":
            unsupported = sorted(numbers(_claims_only(reply)) - numbers(_sources(case, trace)))
            if unsupported:
                return "fail", ", ".join(unsupported), "Reply states figures that appear nowhere in the trace."
            return "pass", "", "Every figure in the reply appears in a source."

        if cid == "uncertainty_signaled":
            if "needs_authority" not in case.tags:
                return "na", "", "No outside authority involved."
            hit = next((a for a in _AUTHORITY if a in low), None)
            if hit:
                return "pass", hit, "Names the gap and who decides."
            hedge = next((h for h in _HEDGE if re.search(rf"\b{h}\b", low)), None)
            if hedge:
                return "partial", hedge, "Hedges without naming the authority."
            return "fail", reply[:120], "Answers as if certain about a jurisdiction-specific requirement."

        if cid == "answers_the_question":
            if case.expect.get("clarify") and "?" in reply:
                return "pass", "", "Asks the question needed to answer."
            # The request is the user's first ask; later turns ("yes, go ahead") are replies to the agent.
            first_ask = next(t["content"] for t in trace.turns if t["role"] == "user")
            ask = _content_words(first_ask)
            overlap = ask & _content_words(reply)
            ratio = len(overlap) / max(1, len(ask))
            ev = ", ".join(sorted(overlap)[:6])
            if ratio >= 0.3:
                return "pass", ev, f"Reply covers the request ({ratio:.0%} term overlap)."
            if ratio >= 0.15:
                return "partial", ev, f"Reply only partly tracks the request ({ratio:.0%} overlap)."
            return "fail", ev, f"Reply drifts from the request ({ratio:.0%} overlap)."

        if cid == "actionable_next_step":
            sents = sentences(reply)
            last_tool = next((t for t in reversed(trace.turns) if t["role"] == "tool"), None)
            if last_tool and last_tool.get("status", "ok") == "ok" and any(_DONE.search(x) for x in sents[:2]):
                done = next(x for x in sents[:2] if _DONE.search(x))
                return "pass", done[:120], "Confirms the action is complete; nothing else needed."
            if any(_IMPERATIVE.search(s) for s in sents) or "?" in reply:
                ev = next((s for s in sents if _IMPERATIVE.search(s) or "?" in s), "")
                return "pass", ev[:120], "Ends with a clear action or choice."
            return "fail", "", "No next action for the user."

        if cid == "plain_language":
            if case.locale != "en":
                avg = len(words(reply)) / max(1, len(sentences(reply)))
                return ("pass" if avg <= 20 else "partial"), f"{avg:.0f} words/sentence", "Sentence length check."
            g = fk_grade(reply)
            v = "pass" if g <= 9 else "partial" if g <= 12 else "fail"
            return v, f"grade {g}", "Flesch-Kincaid proxy for scannability."

        if cid == "respectful_expert":
            b = next((p for p in _BLAME if p in low), None)
            if b:
                return "fail", b, "Blames the user."
            c = next((p for p in _CONDESCEND if re.search(rf"\b{re.escape(p)}\b", low)), None)
            if c:
                return "partial", c, "One condescending phrase."
            return "pass", "", "Peer-to-peer tone."

        return "na", "", "Heuristic judge has no rule for this criterion; use --judge claude."


# ---------------------------------------------------------------- Claude judge

JUDGE_PROMPT = """You are grading one reply from an AI assistant inside professional design software
used by architects, engineers and builders. You are grading ONE criterion only. Ignore every
other quality of the reply, good or bad.

<criterion id="{cid}">
{question}
</criterion>

<scale>
pass: {pass_}
partial: {partial}
fail: {fail}
na: {na}
</scale>

<context_documents>
{docs}
</context_documents>

<conversation>
{transcript}
</conversation>

Grade the assistant's FINAL reply against the criterion, using the conversation and documents
as the only ground truth. Do not use outside knowledge to decide whether a claim is true;
a claim is supported only if the trace supports it. Length and polish are not evidence.

Respond with JSON only, keys in this order:
{{"evidence": "<exact quote from the final reply, or empty>", "reasoning": "<two sentences max>", "verdict": "pass|partial|fail|na"}}"""


def render_transcript(trace: Trace) -> str:
    lines = []
    for t in trace.turns:
        if t["role"] == "tool":
            lines.append(f'[tool result: {t.get("name")} · status={t.get("status", "ok")}] {json.dumps(t.get("content"))}')
        else:
            calls = "".join(f' [calls {c["name"]}({json.dumps(c.get("args", {}))})]' for c in t.get("tool_calls", []) or [])
            lines.append(f'{t["role"].upper()}: {t.get("content", "")}{calls}')
    return "\n".join(lines)


class ClaudeJudge:
    def __init__(self, model: str | None = None):
        try:
            import anthropic  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise SystemExit("pip install anthropic  (and set ANTHROPIC_API_KEY) to use --judge claude") from e
        import anthropic
        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("LINTEL_JUDGE_MODEL", "claude-sonnet-5-5")
        self.name = f"claude:{self.model}"
        self.parse_failures = 0

    def grade(self, case: Case, trace: Trace, rubric: dict, crit: dict) -> tuple[str, str, str]:
        docs = "\n\n".join(f'## {d.get("title", "")}\n{d.get("text", "")}' for d in case.context.get("docs", [])) or "(none)"
        prompt = JUDGE_PROMPT.format(cid=crit["id"], question=crit["question"].strip(), pass_=crit["scale"]["pass"],
                                     partial=crit["scale"]["partial"], fail=crit["scale"]["fail"], na=crit.get("na", "Never."),
                                     docs=docs, transcript=render_transcript(trace))
        msg = self.client.messages.create(model=self.model, max_tokens=400, temperature=0,
                                          messages=[{"role": "user", "content": prompt}])
        raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        try:
            data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
            v = data["verdict"].strip().lower()
            assert v in VERDICTS
            return v, data.get("evidence", ""), data.get("reasoning", "")
        except Exception:
            self.parse_failures += 1
            # A judge that can't produce a verdict is a failed measurement, never a pass.
            return "fail", raw[:120], "JUDGE_PARSE_FAILURE: treat this case as unmeasured."


def prompt_fingerprint() -> str:
    """Hash of the judge prompt. Stored with every run: change the prompt, and scores aren't comparable."""
    return hashlib.sha256(JUDGE_PROMPT.encode()).hexdigest()[:10]


def get_judge(kind: str) -> Judge:
    return ClaudeJudge() if kind == "claude" else HeuristicJudge()


def judge_trace(judge: Judge, case: Case, trace: Trace, rubrics: list[dict]) -> tuple[list[Finding], dict[str, str]]:
    findings, verdicts = [], {}
    for rubric in rubrics:
        for crit in rubric["criteria"]:
            v, ev, reason = judge.grade(case, trace, rubric, crit)
            verdicts[f'{rubric["id"]}.{crit["id"]}'] = v
            f = verdict_to_finding(rubric, crit, v, ev, reason)
            if f:
                findings.append(f)
    return findings, verdicts
