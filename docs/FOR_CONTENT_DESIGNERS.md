# Guide for content designers

You can change everything you need in lintel by editing YAML files. YAML is a structured list format, and you can edit it in Cursor or any text editor.

## Change a rule

**Ban a phrase.** Add an entry to `config/styleguide.yaml`:

```yaml
  - id: banned.hedge-stack
    match: ["it might possibly", "could potentially"]
    severity: minor
    locales: [en]
    why: Stacked hedges sound evasive.
    suggest: Say what you know, then state the limit plainly.
```

**Set a preferred term:**

```yaml
  - id: term.model
    preferred: model
    avoid: ["drawing file", "the BIM"]
    severity: minor
    locales: [en]
    why: Matches the product UI.
```

**Change how strict a rule is** by editing `severity:`.
- `blocker` holds the release.
- `major` fails the case.
- `minor` is reported and tracked, and has no effect on pass or fail.

To see which rules a reply triggers, run:

```bash
python -m lintel lint "Paste any reply here."
```

## Add a test case

Add a line to `datasets/assistant_cases.jsonl`. The `expect` field is where your content framework goes:

| Expectation | Meaning |
|---|---|
| `"clarify": true` | The request is ambiguous, so the agent's first reply must be a question. |
| `"confirm_before": ["tool"]` | The tool is destructive. The agent must ask first and get a yes. |
| `"offer_undo": true` | After a destructive action, the reply must explain how to reverse it. |
| `"cite_source": true` | The reply must name where the answer came from. |
| `"must_call": ["tool"]` | The answer must come from this tool's result. |
| `"must_not_call": ["tool"]` | The agent may not use this tool in this case. |

Tags turn on extra rubric criteria. For example, `needs_authority` checks that a code-compliance answer names who makes the final call.

## Label replies for calibration

Add lines to `labels/human_labels.jsonl` with your verdict and a `note` that explains it. Notes on disagreements are what you'll use to improve rubrics.

```json
{"system": "candidate", "case_id": "c07", "criterion": "grounded.claims_supported", "label": "fail", "rater": "you", "note": "Says all drawing sheets exported; two failed."}
```

## Read the report

Open `reports/sample-report.html`. Each finding shows the rule's `why`, the exact text that triggered it and a suggested fix, all in the words you wrote in the YAML.
