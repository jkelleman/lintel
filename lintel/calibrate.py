"""Evaluate the evaluator.

A judge is a measuring instrument. Before its scores mean anything, check it
against people who know what good looks like. Per criterion, we report raw
agreement AND Cohen's kappa, because raw agreement flatters a judge that
says "pass" to everything on a dataset that's mostly passes.

Rule of thumb used here:
  kappa >= 0.80  trusted: can gate releases on its own
  kappa >= 0.60  usable: gate, but sample disagreements weekly
  kappa <  0.60  not trusted: rewrite the rubric anchors before relying on it
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .models import read_jsonl

TRUSTED, USABLE = 0.80, 0.60


def cohen_kappa(a: list[str], b: list[str]) -> float:
    assert len(a) == len(b) and a, "need paired labels"
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(a) | set(b)) / (n * n)
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    return round((po - pe) / (1 - pe), 3)


def calibrate(verdicts: dict[str, dict[str, str]], labels_path: str) -> list[dict[str, Any]]:
    """Compare judge verdicts to human labels.

    verdicts: {"<system>/<case_id>": {criterion: verdict}}
    labels:   {system, case_id, criterion, label, rater, note}
    """
    human = defaultdict(dict)
    notes = {}
    for row in read_jsonl(labels_path):
        key = f'{row["system"]}/{row["case_id"]}'
        human[row["criterion"]][key] = row["label"]
        notes[(row["criterion"], key)] = row.get("note", "")

    report = []
    for crit, by_case in sorted(human.items()):
        keys = [c for c in by_case if verdicts.get(c, {}).get(crit)]
        if not keys:
            continue
        h, j = [by_case[c] for c in keys], [verdicts[c][crit] for c in keys]
        pairs = list(zip(h, j))
        k = cohen_kappa(h, j)
        disagreements = [
            {"case_id": c, "human": by_case[c], "judge": verdicts[c][crit], "note": notes.get((crit, c), "")}
            for c in keys if verdicts[c][crit] != by_case[c]
        ]
        status = "trusted" if k >= TRUSTED else "usable" if k >= USABLE else "not trusted"
        report.append({"criterion": crit, "n": len(pairs),
                       "agreement": round(sum(x == y for x, y in pairs) / len(pairs), 3),
                       "kappa": k, "status": status, "disagreements": disagreements})
    return report
