# Case study: an eval system that content designers own

**Role:** designer and builder · **Scope:** framework, rules, rubrics, dataset, calibration, CI gate · **Stack:** Python, YAML, optional Claude judge

## The problem

Teams that ship AI assistants usually start evaluating in one of two ways:

1. **A prose linter.** It's cheap and predictable, but it only sees words. It can't see what an agent did.
2. **An LLM judge.** It can grade nuance, but it costs money on every run, its results vary, and teams often trust it without measuring it.

Before a release, a team needs answers to three questions. Is this version safe to put in front of professionals? If it isn't, which words or behaviors are the problem? Who owns the fix?

In professional design software, mistakes have specific costs. If an assistant tells an architect "Done!" after half the drawing sheets failed to export, the architect finds out at the print shop. If an assistant says walls are "fully compliant," it has made a claim that only the local code official can make.

## The approach

Each check goes on the cheapest level that can catch it.

| Decision | Reason | Alternative I rejected |
|---|---|---|
| Four levels, cheapest first | Word lists, shape checks and trace logic catch most failures that matter. Model calls are saved for what needs them. | One large judge prompt. It's slow and costly, and it's hard to debug when it disagrees with people. |
| Rules in YAML, each with a `why` | Content designers own voice, terminology and severity. The report prints the `why` so each finding explains itself. | Rules written in Python, where every wording change needs an engineer. |
| Severity levels set by content design | A compliance overclaim is a blocker. A minimizer like "simply" is minor. Deciding that is a product call. | One pass/fail score, where every issue looks equally urgent. |
| Contracts as their own level | A recovery framework (what happened, why, what's safe, what to do next) describes the shape of a reply. A script can check that. | Leaving it to the judge, which gives inconsistent results on the most rule-based part of content design. |
| Checks on the full trace | Many agent failures are actions: deleting without asking, acting on a guess, rounding a partial result up to success. | Grading only the final message, which misses what the user actually experienced. |
| One criterion per judge call | When a prompt grades several criteria at once, a fluent reply tends to pass everything, including accuracy. | Multi-criterion judge prompts. |
| Evidence quote and reasoning before the verdict, temperature 0, parse failures count as failures | Every verdict can be audited, and a case the judge couldn't grade is recorded as a fail. | Free-form judge output. |
| Cohen's κ per criterion | If most cases pass, a judge that always says "pass" gets high raw agreement. κ corrects for agreement by chance. | Reporting percent agreement alone. |
| Per-case gate for high-risk cases | An average can hide the one regression that matters most. | A pass-rate threshold alone. |
| Prompt hash and rubric versions in every report | Changing the judge changes what's being measured, so scores from before and after can't be compared. | Untracked prompt edits. |

## What the sample run shows

- **Baseline: 2 of 12 cases pass. Candidate: 11 of 12 pass.** On average, the candidate is much better.
- **The gate holds the candidate.** In case c07, after a partial export failure, the candidate says "Done!" Two levels catch this on their own. The trajectory check flags a blocker for the false success claim, and the contract check flags the missing recovery details. Neither needs a model judge.
- **The report shows where the judge can be trusted.** On `claims_supported`, the heuristic judge agrees with human labels 88% of the time, but κ is 0.59, which is below the threshold for gating. Its disagreements show what it can't do:
  - It treats advice ("try 300 DPI") as a claim about the model.
  - It misses a false claim that has no numbers in it ("I undid the roof change," when the tool undid a door move).
  - It passes c07 because the drawing sheet numbers match the trace, even though the claim is false.

  An LLM judge should handle these cases better, and calibration is how you'd confirm that after switching.
- On `answers_the_question`, κ is 0.13. Term overlap fails across languages, and it can't tell when an agent acted on a guess. This criterion needs a better rubric or a model judge before it gates anything.

## What I'd do next with a team

1. **Put the team's style guide into level 1** and run it on a week of production traces. Find the noisiest rules and tune their severity with the people who own the words.
2. **Write contracts for the three or four situations that matter most:** errors, destructive actions, compliance questions and handoffs to a person.
3. **Have two reviewers label 50 to 100 traces** for each high-stakes criterion. Check the reviewers' agreement first. If they disagree, the rubric needs work before a model judge can use it.
4. **Add the gate to CI** for prompt, model and tool changes, with the HTML report attached for content review.
5. **Hold a weekly disagreement review.** Compare judge and human verdicts, version each rubric edit, and track κ over time.

## How this connects to my past work

At Microsoft I led the Fabric Unified Error Framework, and lintel's recovery contract is adapted from its four-field error envelope. I've also trained human reviewers and LLM judges to grade AI output consistently, which is where the calibration step comes from. In my experience, the hardest part of evals is getting people to agree on what good looks like, and then showing that the grader agrees with them too.
