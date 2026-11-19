"""Rung 2: response contracts. Situation-aware shape checks on a reply."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Case, Finding, Trace
from .text import guess_language


FIELD_NAMES = {"what_happened": "what happened", "why": "why", "state_of_work": "what's safe", "next_step": "what to do next"}


def load_contracts(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _has_any(text: str, signals: list[str]) -> str | None:
    low = text.lower()
    return next((s for s in signals if s in low), None)


def _reply_after(trace: Trace, idx: int) -> tuple[int, str] | None:
    for j in range(idx + 1, len(trace.turns)):
        t = trace.turns[j]
        if t["role"] == "assistant" and t.get("content"):
            return j, t["content"]
    return None


def check_contracts(case: Case, trace: Trace, cfg: dict[str, Any]) -> list[Finding]:
    out: list[Finding] = []
    loc = case.locale

    # 1. Recovery envelope after a failed or partial tool result.
    env = cfg["recovery_envelope"]
    for i, t in enumerate(trace.turns):
        if t["role"] == "tool" and t.get("status") in ("error", "partial"):
            nxt = _reply_after(trace, i)
            if not nxt:
                out.append(Finding("contract", "recovery.no-reply", "blocker", False,
                                   "A tool failed and the assistant didn't tell the user.", turn=i))
                break
            j, reply = nxt
            missing = [name for name, sig in env["fields"].items() if not _has_any(reply, sig.get(loc, sig["en"]))]
            out.append(Finding(
                "contract", "recovery.envelope", env["severity"], not missing,
                env["why"] if missing else "All four recovery fields present.",
                evidence=("Missing: " + ", ".join(FIELD_NAMES.get(m, m) for m in missing)) if missing else "", turn=j,
                suggestion="Say what happened, why (or that you don't know), what's safe, and what to do next."
                if missing else ""))
            break  # one envelope check per trace: the first failure is the moment of truth

    # 2. Reply language matches the user's locale.
    final = trace.final_reply()
    lang = guess_language(final)
    ok = lang in (loc, "unknown")
    out.append(Finding("contract", "locale.match", cfg["locale_match"]["severity"], ok,
                       cfg["locale_match"]["why"] if not ok else f"Reply language matches locale ({loc}).",
                       evidence="" if ok else f"expected {loc}, got {lang}"))

    # 3. Source attribution when the answer must be grounded in provided docs.
    if case.expect.get("cite_source"):
        sa = cfg["source_attribution"]
        hit = _has_any(final, sa["signals"].get(loc, sa["signals"]["en"]))
        out.append(Finding("contract", "grounding.attribution", sa["severity"], bool(hit),
                           f'Cites its source ("{hit}").' if hit else sa["why"],
                           suggestion="" if hit else "Name the help topic, document or RFI the answer came from."))
    return out
