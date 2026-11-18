"""Rung 1: the prose linter. Where this project started.

Fast, free, deterministic. Runs on every assistant message, every commit.
If a rule can be written as a word list or a count, it belongs here, not in an LLM judge.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .models import Finding
from .text import fk_grade, sentences, words

_PASSIVE = re.compile(r"\b(?:was|were|been|being|is|are|be)\s+\w+(?:ed|en)\s+by\b", re.I)


def load_styleguide(path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _applies(rule: dict[str, Any], locale: str) -> bool:
    locales = rule.get("locales")
    return not locales or locale in locales


def _find_phrase(text: str, phrase: str) -> str | None:
    m = re.search(rf"(?<![\w']){re.escape(phrase)}(?![\w'])", text, flags=re.I)
    return m.group(0) if m else None


def lint_text(text: str, guide: dict[str, Any], locale: str = "en", turn: int | None = None) -> list[Finding]:
    """Return only failures. Lint is noisy by nature; passes add nothing to a report."""
    out: list[Finding] = []

    for rule in guide.get("phrases", []):
        if not _applies(rule, locale):
            continue
        for phrase in rule["match"]:
            hit = _find_phrase(text, phrase)
            if hit:
                out.append(Finding("lint", rule["id"], rule["severity"], False,
                                   rule["why"], evidence=hit, turn=turn, suggestion=rule.get("suggest", "")))
                break

    for rule in guide.get("terminology", []):
        if not _applies(rule, locale):
            continue
        for bad in rule["avoid"]:
            hit = _find_phrase(text, bad)
            if hit:
                out.append(Finding("lint", rule["id"], rule["severity"], False, rule["why"],
                                   evidence=hit, turn=turn, suggestion=f'Use "{rule["preferred"]}".'))
                break

    s = guide.get("structure", {})
    total_words = len(words(text))
    if total_words > s.get("max_reply_words", 10_000):
        out.append(Finding("lint", "structure.reply-length", "major", False,
                           "Reply is long enough to bury the action the user needs.",
                           evidence=f"{total_words} words (limit {s['max_reply_words']})", turn=turn,
                           suggestion="Lead with the answer or the action. Move detail behind a link."))

    limit = s.get("max_sentence_words")
    if limit:
        for sent in sentences(text):
            n = len(words(sent))
            if n > limit:
                out.append(Finding("lint", "structure.sentence-length", "minor", False,
                                   "Long sentences are harder to scan mid-task.",
                                   evidence=sent[:120] + ("…" if len(sent) > 120 else ""), turn=turn,
                                   suggestion=f"Split it. {n} words, limit {limit}."))
                break  # one per message is enough signal

    if text.count("!") > s.get("max_exclamations", 99):
        out.append(Finding("lint", "structure.exclamations", "minor", False,
                           "Exclamation points read as hype in a professional tool.",
                           evidence=f'{text.count("!")} found', turn=turn))

    if locale == "en" and s.get("max_fk_grade"):
        grade = fk_grade(text)
        if grade > s["max_fk_grade"]:
            out.append(Finding("lint", "structure.reading-grade", "minor", False,
                               "Reading level is higher than the target for in-product help.",
                               evidence=f"grade {grade} (target ≤ {s['max_fk_grade']})", turn=turn))

    if locale == "en" and s.get("passive_voice"):
        m = _PASSIVE.search(text)
        if m:
            out.append(Finding("lint", "structure.passive-voice", s["passive_voice"], False,
                               "Passive voice can hide who did what — the agent or the user.",
                               evidence=m.group(0), turn=turn))
    return out
