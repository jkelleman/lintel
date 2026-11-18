# Writing rubrics a judge can actually follow

A rubric is UX writing for a grader. The same rules apply as for any interface text: one job per element, concrete language, no ambiguity about what to do next.

## Rules I follow

1. **One criterion per judge call.** If you're tempted to write "accurate and well-written," that's two criteria.
2. **Ask a question with an answer.** "Is every specific claim supported by the trace?" beats "Rate accuracy."
3. **Three anchored levels plus N/A, not 1–10.** `pass / partial / fail / na`. A 7 and an 8 can't be told apart, by people or by models.
4. **Anchor with observable behavior.** "Names the gap and the authority (e.g., the local code official)" is gradable. "Handles uncertainty well" isn't.
5. **Say when it doesn't apply.** Without an explicit `na`, judges invent a verdict. `uncertainty_signaled` is N/A unless the case is tagged `needs_authority`.
6. **Define the ground truth.** "Use the conversation and documents as the only ground truth. Don't use outside knowledge." Otherwise the judge grades against its own training data.
7. **Require evidence, then reasoning, then the verdict.** A quote from the reply anchors the grade, and putting reasoning first stops the judge from justifying a verdict it already picked.
8. **Tell it what doesn't count.** "Length and polish are not evidence." This counters verbosity bias.
9. **Set severity per criterion.** Failing `claims_supported` is a blocker. Failing `plain_language` is minor.
10. **Version every edit.** Bump `version:` whenever the anchors change, and re-run calibration.

## The loop

```
write rubric → label 50+ traces (two raters) → check inter-rater κ
     ↑                                                   ↓
 revise anchors  ←  read disagreements  ←  run judge, compute judge-vs-human κ
```

If two people can't agree (κ < 0.6 between raters), the problem is the rubric, not the judge. Fix the anchors before you spend anything on model calls.

## Template

```yaml
id: my_rubric
name: Human-readable name
version: 1
criteria:
  - id: criterion_id
    severity: blocker | major | minor
    question: >
      One question, answerable from the trace alone.
    scale:
      pass: Observable behavior that earns a pass.
      partial: The specific way it falls short.
      fail: The behavior that's never acceptable.
    na: When this criterion doesn't apply, or "Never."
```
