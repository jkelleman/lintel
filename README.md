# lintel

**From prose linter to agent evals: a content-owned eval ladder for AI assistants in design software.**

A lintel is the beam over an opening that carries the load. This one carries a content style guide all the way up to release gates for agents.

> Inspired by the Autodesk content design leadership. lintel grows a simple prose linter into an eval system for agents, with an AEC assistant as the sample domain.

```
python -m lintel run runs/candidate.jsonl --baseline runs/baseline.jsonl

lintel · candidate · judge=heuristic-v1
  11/12 cases pass (92%)
  regressed c07 Export sheets to PDF (partial failure)
  fixed     c02 Purge unused families   … and 9 more
  judge κ  0.59  not trusted grounded.claims_supported
  judge κ  0.81  trusted     useful.actionable_next_step
  judge κ  0.13  not trusted useful.answers_the_question

  GATE: HOLD
   - 1 blocker finding(s); limit is 0
   - high-risk regression on c07 (Export sheets to PDF (partial failure))
```

**The headline:** the new agent version improves from 17% to 92% of cases passing, and it still doesn't ship, because it now tells an architect that a half-failed sheet export succeeded. An average would have shipped it. A content-owned gate didn't.

[Sample report (HTML)](reports/sample-report.html) · [Case study](docs/CASE_STUDY.md) · [Why this matters at Autodesk](docs/WHY_AUTODESK.md)

---

## The ladder

Each rung costs more and judges more nuance. Push every check as far *down* the ladder as it will go.

| Rung | What it checks | Owned in | Cost | Example catch |
|---|---|---|---|---|
| **1 · Lint** | Words, terms, length, reading level, voice | [`config/styleguide.yaml`](config/styleguide.yaml) | Free, instant, deterministic | "fully compliant" → **blocker** (compliance overclaim) |
| **2 · Contracts** | The *shape* a reply must take in a situation | [`config/contracts.yaml`](config/contracts.yaml) | Free | After a tool error: what happened · why · what's safe · what to do next |
| **3 · Trajectory** | What the agent *did*: tool calls, order, honesty | [`lintel/trajectory.py`](lintel/trajectory.py) + case expectations | Free | Ran `purge_unused` without asking; said "Done!" after a partial failure |
| **4 · Judge** | Nuance: grounding, usefulness, voice | [`rubrics/*.yaml`](rubrics) | Model calls | "16 clashes" when the tool returned 14 |
| **Meta** | Is the judge itself trustworthy? | [`labels/human_labels.jsonl`](labels/human_labels.jsonl) | Human time | κ 0.59 → don't gate on this criterion yet |

Rungs 1–3 catch most of the failures that matter in professional tools, and they cost nothing to run. The model judge is reserved for what only a model can see, and it isn't trusted until it agrees with people.

## What makes this more than a linter

- **Content design owns the rules.** The style guide, contracts, rubrics and severities are YAML with a `why` on every rule. The report quotes that `why` back, so findings teach instead of nag. See [For content designers](docs/FOR_CONTENT_DESIGNERS.md).
- **Severity is a product decision.** `blocker` holds the release, `major` fails the case, `minor` is tracked. A compliance overclaim in AEC is a liability, not a style nit, so it's a blocker on rung 1.
- **It evaluates actions, not just words.** Confirmation before destructive tools, clarifying before acting on ambiguity, honest reporting of partial results, offering undo. A beautifully written reply can still be a failure.
- **It evaluates the evaluator.** Per-criterion Cohen's κ against human labels, with every disagreement logged with a reason. The sample shows why raw agreement lies: 88% agreement, κ 0.59.
- **Averages don't gate releases.** High-risk cases are gated one by one against the baseline. A regression on a high-risk case holds the release no matter how good the average looks.
- **Runs are reproducible.** Every report records the judge, a hash of the judge prompt and each rubric version. If you change the prompt, scores from before and after aren't comparable, and the report shows it.
- **Locale-aware.** English word lists never fire on a Spanish reply. Reply language must match the user's locale (blocker).

## Quick start

```bash
pip install -e ".[dev]"
pytest -q                                   # 13 tests, each one states a rule

python -m lintel lint "Simply click on Export. It's guaranteed to work!"
python -m lintel run runs/candidate.jsonl --baseline runs/baseline.jsonl   # writes reports/
python -m lintel calibrate runs/baseline.jsonl runs/candidate.jsonl
```

Everything runs offline with a deterministic heuristic judge, so it works in CI with no API key. To use an LLM judge:

```bash
pip install -e ".[claude]" && export ANTHROPIC_API_KEY=...
python -m lintel run runs/candidate.jsonl --baseline runs/baseline.jsonl --judge claude
python -m lintel calibrate runs/*.jsonl --judge claude   # does it beat the heuristic's κ?
```

The heuristic is also the floor. If an LLM judge can't beat the heuristic's agreement with humans on a criterion, the rubric is the problem, not the model.

## The sample domain

Twelve cases for a fictional assistant inside BIM authoring software ([`datasets/assistant_cases.jsonl`](datasets/assistant_cases.jsonl)): section views, purging families, ambiguous renames, failed uploads, clash detection, corridor fire ratings, partial PDF exports, RFIs, stair compliance, a Spanish-language how-to, undo, and slow renders. Each case has a `baseline` and a `candidate` trace with tool calls and tool results ([`runs/`](runs)).

All sample data is fictional and illustrative. Human labels were written for this demo to show the calibration loop, not taken from a real rater pool.

## Repo map

```
config/      styleguide.yaml · contracts.yaml       ← content-owned rules
rubrics/     grounded · useful · voice              ← one criterion per judge call
datasets/    assistant_cases.jsonl                  ← cases + expectations
runs/        baseline.jsonl · candidate.jsonl       ← agent traces (any agent, any framework)
labels/      human_labels.jsonl                     ← for judge calibration
lintel/      lint · contracts · trajectory · judge · calibrate · runner · report · cli
reports/     sample-report.{html,md,json}
docs/        case study · writing rubrics · for content designers · why Autodesk
.cursor/     rules for extending lintel in Cursor
```

## Roadmap

- **MCP trace adapter**: convert MCP client logs (for example, from an agent built on Autodesk Platform Services MCP servers) into lintel traces, so any MCP agent can be put through the ladder.
- **Write-tool policy pack**: a contract set for agents that modify models, where every write needs confirmation, a scoped summary and an undo path.
- **Pairwise judging** with position swapping, for A/B prompt comparisons.
- **Disagreement queue**: route judge/human disagreements to a weekly rubric review, and track κ over time.
- **Vale export**: emit rung 1 as a Vale style, so the same rules run in docs pipelines.

---

Built by [Jen Kelleman](https://github.com/jkelleman), a conversation and content designer for AI agents. MIT licensed.
