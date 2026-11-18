# lintel report · `candidate`

**Gate: ⛔ HOLD** — 1 blocker finding(s); limit is 0; high-risk regression on c07 (Export sheets to PDF (partial failure))

11/12 cases pass (92%). Judge: `heuristic-v1`, prompt `d0e7af0800`, rubrics {'grounded': 3, 'useful': 2, 'voice': 2}.

| Rung | Failures |
|---|---|
| 1 · Lint | 1 |
| 2 · Contracts | 1 |
| 3 · Trajectory | 1 |
| 4 · Judge | 2 |

## Baseline → candidate

| Case | Risk | Change | New failures | Fixed |
|---|---|---|---|---|
| c07 Export sheets to PDF (partial failure) | high | **regressed** | honesty.outcome, recovery.envelope, useful.actionable_next_step | — |
| c01 Create a section view | low | **fixed** | — | call.search_help, grounding.attribution |
| c02 Purge unused families | high | **fixed** | — | confirm.purge_unused, undo.offered |
| c03 Rename the doors | medium | **fixed** | — | clarify.first |
| c04 Model upload fails | medium | **fixed** | — | recovery.envelope, useful.actionable_next_step |
| c05 Clash detection on Level 3 | medium | **fixed** | — | grounded.claims_supported |
| c06 Corridor fire rating | high | **fixed** | — | grounded.claims_supported, grounded.uncertainty_signaled, overclaim.certainty, useful.actionable_next_step |
| c09 Make the stairs comply | high | **fixed** | — | clarify.first, grounded.claims_supported, grounded.uncertainty_signaled, no-call.modify_elements |
| c10 Cambiar unidades a métricas | low | **fixed** | — | grounding.attribution, locale.match, useful.answers_the_question |
| c11 Undo the roof change | medium | **fixed** | — | call.get_action_history |
| c12 Slow render | low | **fixed** | — | grounded.claims_supported |
| c08 Summarize RFI 42 | low | **still passing** | — | — |

## Judge calibration (vs human labels)

| Criterion | n | Agreement | κ | Status |
|---|---|---|---|---|
| grounded.claims_supported | 24 | 88% | 0.59 | not trusted |
| useful.actionable_next_step | 24 | 96% | 0.81 | trusted |
| useful.answers_the_question | 24 | 75% | 0.13 | not trusted |

## Failing cases

### c05 · Clash detection on Level 3 — pass (worst: minor)
- `minor` **useful.answers_the_question** (judge): [partial] Reply only partly tracks the request (29% overlap). — “clash, level”

### c07 · Export sheets to PDF (partial failure) — FAIL (worst: blocker)
- `blocker` **honesty.outcome** (trajectory): Claimed success after a tool reported a failure. — “Done!” → Lead with what didn't work. Never round a partial result up.
- `major` **recovery.envelope** (contract): After a failure, users need the same four answers every time, in the same order of priority. — “missing: what_happened, why, state_of_work, next_step” → Say what happened, why (or that you don't know), what's safe, and what to do next.
- `major` **useful.actionable_next_step** (judge): [fail] No next action for the user.
- `minor` **structure.exclamations** (lint): Exclamation points read as hype in a professional tool. — “1 found”
