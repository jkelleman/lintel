# Writing rubrics a judge can follow

A rubric is interface text for a grader. The same principles apply as for any UI copy: each element has one job, the language is concrete, and the next step is clear.

## Guidelines

1. **Grade one criterion per judge call.** "Accurate and well written" is two criteria, so split it.
2. **Ask a question with a clear answer.** "Is every specific claim supported by the trace?" works better than "Rate accuracy."
3. **Use three anchored levels plus N/A.** `pass / partial / fail / na` is easier to apply consistently than a 1–10 scale. People and models both struggle to tell a 7 from an 8.
4. **Describe observable behavior in the anchors.** "Names the gap and the authority (for example, the local code official)" can be graded. "Handles uncertainty well" is too vague.
5. **Say when a criterion doesn't apply.** Without an explicit `na`, a judge will make up a verdict. `uncertainty_signaled` is N/A unless the case is tagged `needs_authority`.
6. **Define the source of truth.** Tell the judge to use only the conversation and the provided documents. Otherwise it grades against its own training data.
7. **Ask for evidence first, then reasoning, then the verdict.** A quote from the reply anchors the grade. Reasoning that comes before the verdict keeps the judge from justifying a verdict it already picked.
8. **Tell the judge what to ignore.** "Length and polish are not evidence" reduces the bias toward longer replies.
9. **Set severity for each criterion.** Failing `claims_supported` is a blocker. Failing `plain_language` is minor.
10. **Version every change.** Bump `version:` whenever the anchors change, then rerun calibration.

## The loop

```
write rubric → two people label 50+ traces → check their agreement (κ)
     ↑                                                     ↓
 revise anchors  ←  read disagreements  ←  run the judge, compare it with the labels
```

If the two reviewers agree with each other below κ 0.6, fix the rubric anchors before spending money on model calls.

## Template

```yaml
id: my_rubric
name: Human-readable name
version: 1
criteria:
  - id: criterion_id
    severity: blocker | major | minor
    question: >
      One question that can be answered from the trace alone.
    scale:
      pass: The observable behavior that earns a pass.
      partial: The specific way the reply falls short.
      fail: The behavior that is never acceptable.
    na: When this criterion doesn't apply, or "Never."
```
