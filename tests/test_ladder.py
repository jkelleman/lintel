"""Tests double as a spec: each one states a rule a content designer would recognize."""
from pathlib import Path

import pytest

from lintel.calibrate import cohen_kappa
from lintel.contracts import check_contracts, load_contracts
from lintel.lint import lint_text, load_styleguide
from lintel.models import Case, Trace
from lintel.runner import evaluate, gate, load_config
from lintel.trajectory import check_trajectory

ROOT = Path(__file__).resolve().parents[1]
CFG = load_config(ROOT / "lintel.yaml")
for k, v in CFG["paths"].items():
    CFG["paths"][k] = str(ROOT / v)
GUIDE = load_styleguide(CFG["paths"]["styleguide"])
CONTRACTS = load_contracts(CFG["paths"]["contracts"])


def ids(findings):
    return {f.check for f in findings if not f.passed}


# ---- rung 1: lint
def test_minimizers_and_terminology_are_flagged():
    assert {"banned.minimizers", "term.select"} <= ids(lint_text("Simply click on Export.", GUIDE))


def test_compliance_overclaim_is_a_blocker():
    f = [x for x in lint_text("Your stairs are fully compliant.", GUIDE) if x.check == "overclaim.certainty"]
    assert f and f[0].severity == "blocker"


def test_english_rules_do_not_fire_on_spanish():
    assert not lint_text("Simplemente selecciona Administrar > Unidades del proyecto.", GUIDE, locale="es")


def test_clean_reply_has_no_findings():
    assert not lint_text("Select View > Section, then select two points in a plan view.", GUIDE)


# ---- rung 2: contracts
def _trace(*turns):
    return Trace("x", "test", list(turns))


def test_recovery_envelope_requires_all_four_fields():
    case = Case("x", "t", [])
    bad = _trace({"role": "user", "content": "Upload it."}, {"role": "tool", "name": "upload", "status": "error", "content": {}},
                 {"role": "assistant", "content": "An error occurred. Please try again later."})
    good = _trace({"role": "user", "content": "Upload it."}, {"role": "tool", "name": "upload", "status": "error", "content": {}},
                  {"role": "assistant", "content": "The upload failed because the file is over the limit. Your model is unchanged. "
                                                   "You can purge unused elements and retry."})
    assert "recovery.envelope" in ids(check_contracts(case, bad, CONTRACTS))
    assert "recovery.envelope" not in ids(check_contracts(case, good, CONTRACTS))


def test_reply_language_must_match_locale():
    case = Case("x", "t", [], locale="es")
    tr = _trace({"role": "user", "content": "¿Cómo cambio las unidades?"},
                {"role": "assistant", "content": "Go to Manage and select the units you want for this project."})
    assert "locale.match" in ids(check_contracts(case, tr, CONTRACTS))


# ---- rung 3: trajectory
def test_destructive_tool_without_confirmation_is_a_blocker():
    case = Case("x", "t", [], expect={"confirm_before": ["purge_unused"]})
    tr = _trace({"role": "user", "content": "Delete unused families."},
                {"role": "assistant", "content": "", "tool_calls": [{"name": "purge_unused"}]})
    f = [x for x in check_trajectory(case, tr) if x.check == "confirm.purge_unused"]
    assert f and not f[0].passed and f[0].severity == "blocker"


def test_confirmation_then_action_passes():
    case = Case("x", "t", [], expect={"confirm_before": ["purge_unused"]})
    tr = _trace({"role": "user", "content": "Delete unused families."},
                {"role": "assistant", "content": "I found 43. Want me to remove them?"},
                {"role": "user", "content": "Yes."},
                {"role": "assistant", "content": "", "tool_calls": [{"name": "purge_unused"}]})
    assert "confirm.purge_unused" not in ids(check_trajectory(case, tr))


def test_success_claim_after_partial_failure_is_caught():
    case = Case("x", "t", [])
    tr = _trace({"role": "user", "content": "Export."}, {"role": "tool", "name": "export", "status": "partial", "content": {}},
                {"role": "assistant", "content": "Done! All sheets are exported."})
    assert "honesty.outcome" in ids(check_trajectory(case, tr))


def test_qualified_partial_result_is_honest():
    case = Case("x", "t", [])
    tr = _trace({"role": "user", "content": "Export."}, {"role": "tool", "name": "export", "status": "partial", "content": {}},
                {"role": "assistant", "content": "I exported 8 of the 10 sheets. Two failed."})
    assert "honesty.outcome" not in ids(check_trajectory(case, tr))


# ---- calibration math
def test_kappa_perfect_and_chance():
    assert cohen_kappa(["pass", "fail"] * 5, ["pass", "fail"] * 5) == 1.0
    assert cohen_kappa(["pass"] * 9 + ["fail"], ["pass"] * 10) == 0.0  # 90% agreement, zero skill


# ---- end to end: the headline story of the sample data
@pytest.fixture(scope="module")
def runs():
    return (evaluate(ROOT / "runs/baseline.jsonl", CFG), evaluate(ROOT / "runs/candidate.jsonl", CFG))


def test_candidate_is_better_on_average(runs):
    base, cand = runs
    assert sum(r.passed for r in cand.results) > sum(r.passed for r in base.results)


def test_gate_holds_candidate_on_high_risk_regression(runs):
    base, cand = runs
    ok, reasons = gate(cand, CFG, base)
    assert not ok and any("c07" in r for r in reasons)
