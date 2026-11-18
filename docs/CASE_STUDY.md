# Case study: a content-owned eval ladder

**Role:** designer and builder · **Scope:** framework, rules, rubrics, dataset, calibration, CI gate · **Stack:** Python, YAML, optional Claude judge

## The problem

Teams shipping AI assistants usually start evals in one of two places:

1. **A prose linter.** Cheap and trusted, but blind to what an agent *does*.
2. **An LLM judge.** Sees nuance, but it's expensive and non-deterministic, and teams tend to trust it without ever measuring it.

Neither tells a team what it needs to know before release: **is this version safe to put in front of professionals, and if not, which words or behaviors are the problem, and who owns the fix?**

In professional design software the stakes are specific. An architect who's told "Done!" after half the sheets failed to export finds out at the print shop. An assistant that says walls are "fully compliant" has made a claim only the authority having jurisdiction can make.

## The approach: push every check as far down the ladder as it will go

| Decision | Why | Rejected alternative |
|---|---|---|
| Four rungs, cheapest first | Most failures that matter are detectable with word lists, shape checks and trace logic. Spend model calls only on what needs them. | One big LLM judge prompt: slow, costly, and hard to debug when it disagrees with people. |
| Rules live in YAML with a `why` | Content designers own voice, terminology and severity. The report quotes the `why` back so findings teach. | Rules in Python: every wording change needs an engineer. |
| Severity tiers, set by content | A compliance overclaim is a blocker, a minimizer is minor. That's a product judgment. | One pass/fail score: everything ends up equally urgent, so nothing is. |
| **Contracts** as their own rung | A recovery framework (what happened, why, what's safe, what next) is a promise about *shape*. It's enforceable without a model. | Leaving it to the judge: you get inconsistent results on the most rule-like part of content design. |
| Trajectory checks on full traces | Agents fail through actions: unconfirmed deletes, guessing at ambiguity, rounding partial results up. | Grading the final message only. That misses what users actually experience. |
| One criterion per judge call | Bundled criteria cause halo effects: fluent replies pass accuracy. | Multi-criterion prompts. |
| Evidence quote + reasoning before verdict, temperature 0, parse failures counted as failures | Makes judge output auditable, and an unmeasured case never silently passes. | Free-form judge output. |
| Cohen's κ per criterion, not raw agreement | On a dataset that's mostly passes, a judge that always says "pass" looks great on agreement. κ corrects for chance. | Reporting % agreement. |
| Gate on high-risk regressions per case | Averages hide the one regression that matters. | Pass-rate threshold only. |
| Prompt hash and rubric versions in every report | Changing the judge changes the ruler. Scores across rulers aren't comparable. | Untracked prompt edits. |

## What the sample run shows

- **Baseline: 2 of 12 pass. Candidate: 11 of 12 pass.** On average it's a big win.
- **Gate: HOLD.** The candidate regressed on c07: after a partial export failure it says "Done!" Two rungs catch it independently. Trajectory flags the honesty blocker, and contracts flag the missing recovery envelope. The model judge isn't needed for either.
- **The judge isn't trusted everywhere, and the report says so.** `claims_supported` agrees with human labels 88% of the time but scores κ 0.59. Its disagreements are instructive:
  - it can't tell a recommendation ("try 300 DPI") from a claim about the model;
  - it misses a wrong claim with no numbers in it ("I undid the roof change" when the tool undid a door move);
  - it passes c07 because the sheet numbers match even though the claim is false.
  
  These are exactly the cases to send to an LLM judge, and exactly what to re-measure after switching.
- `answers_the_question` scores κ 0.13. Term overlap can't see across languages or tell "acted on a guess" from "answered." Don't gate on it until the rubric or the judge changes.

## What I'd do next with a team

1. **Port the team's style guide to rung 1** and run it on a week of production traces to find the noisiest rules. Tune severities with the people who own the words.
2. **Write contracts for the three or four situations that matter most**: errors, destructive actions, compliance questions, handoffs to a human.
3. **Label 50–100 traces per high-stakes criterion** with two raters. Measure inter-rater κ first, because if people don't agree, the rubric isn't ready for a model judge.
4. **Wire the gate into CI** for prompt, model and tool changes, with the HTML report attached for content review.
5. **Run a weekly disagreement review**: judge vs. human, rubric edits versioned, κ tracked over time.

## How this connects to my work

At Microsoft I led the Fabric Unified Error Framework. lintel's recovery contract is adapted from its four-field error envelope. I've also trained human reviewers and LLM judges to grade AI output consistently, which is where the calibration rung comes from: the hardest part of evals is agreeing on what "good" means, then proving the grader agrees too.
