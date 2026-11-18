"""Small, dependency-free text utilities. Deterministic on purpose."""
from __future__ import annotations

import re

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9¿¡\"'(])")
_WORD = re.compile(r"[A-Za-zÀ-ÿ']+")
# Standalone figures only: "14 clashes", "2.4 GB", "C/4". Skips IDs like W18 or A107.
_NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?")


def strip_markdown(text: str) -> str:
    text = re.sub(r"`[^`]*`", " CODE ", text)
    text = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", text, flags=re.M)
    return text.replace("**", "").replace("__", "")


def sentences(text: str) -> list[str]:
    out = []
    for block in strip_markdown(text).splitlines():
        block = block.strip()
        if not block:
            continue
        out.extend(s.strip() for s in _SENT_SPLIT.split(block) if s.strip())
    return out


def words(text: str) -> list[str]:
    return _WORD.findall(text)


def numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in _NUMBER.findall(text)}


def syllables(word: str) -> int:
    w = word.lower().strip("'")
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def fk_grade(text: str) -> float:
    """Flesch-Kincaid grade level. Crude, but stable and explainable."""
    sents = sentences(text)
    ws = words(" ".join(sents))
    if not sents or not ws:
        return 0.0
    syl = sum(syllables(w) for w in ws)
    return round(0.39 * (len(ws) / len(sents)) + 11.8 * (syl / len(ws)) - 15.59, 1)


_ES_MARKERS = {"el", "la", "los", "las", "de", "que", "para", "una", "con", "por", "puedes", "selecciona", "cómo"}
_EN_MARKERS = {"the", "and", "to", "of", "you", "your", "for", "with", "this", "select", "can"}


def guess_language(text: str) -> str:
    toks = [w.lower() for w in words(text)]
    es = sum(t in _ES_MARKERS for t in toks)
    en = sum(t in _EN_MARKERS for t in toks)
    if es == en == 0:
        return "unknown"
    return "es" if es > en else "en"
