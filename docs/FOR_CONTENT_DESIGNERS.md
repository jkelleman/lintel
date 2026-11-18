# For content designers: you own this, no Python required

"Technical" is a spectrum. Everything you need to change in lintel is a YAML file, which is just a structured list. Open it in Cursor or any editor.

## Change a rule

**Ban a phrase.** Add an entry to `config/styleguide.yaml`:

```yaml
  - id: banned.hedge-stack
    match: ["it might possibly", "could potentially"]
    severity: minor
    locales: [en]
    why: Stacked hedges sound evasive. Pick one, or state the limit plainly.
    suggest: Say what you know and what you don't.
```

**Prefer a term:**

```yaml
  - id: term.model
    preferred: model
    avoid: ["drawing file", "the BIM"]
    severity: minor
    locales: [en]
    why: Matches product UI.
```

**Change how strict something is.** Edit `severity:`.
- `blocker` holds the release.
- `major` fails the case.
- `minor` is reported and tracked, but doesn't fail anything.

Then run:

```bash
python -m lintel lint "Paste any reply here to see what fires."
```

## Add a test case

Add a line to `datasets/assistant_cases.jsonl`. The `expect` field is where your content framework lives:

| Expectation | Means |
|---|---|
| `"clarify": true` | The request is ambiguous. The first reply must be a question, not an action. |
| `"confirm_before": ["tool"]` | This tool is destructive. The agent must ask and get a yes first. |
| `"offer_undo": true` | After a destructive action, say how to reverse it. |
| `"cite_source": true` | The answer must name where it came from. |
| `"must_call": ["tool"]` | The answer must be grounded in this tool, not the model's memory. |
| `"must_not_call": ["tool"]` | This tool is out of bounds here. |

Tags like `needs_authority` switch on rubric criteria (for example, "names who decides" for code-compliance questions).

## Label for calibration

Add lines to `labels/human_labels.jsonl` with your verdict and, most importantly, a `note` explaining it. Notes on disagreements are how rubrics get better.

```json
{"system": "candidate", "case_id": "c07", "criterion": "grounded.claims_supported", "label": "fail", "rater": "you", "note": "Says all sheets exported; two failed."}
```

## Read the report

Open `reports/sample-report.html`. Every finding has the rule's `why`, the exact text that triggered it, and a suggested fix, all written in your language, because you wrote it.
