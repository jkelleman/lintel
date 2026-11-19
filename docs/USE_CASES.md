# Use cases

This page covers who uses lintel, when, and how. Each use case lists the people involved, the problem, the steps with the files and commands, what you end up with, and what to watch for.

Each use case has a status:

- **Ready now:** works with the repo as it is.
- **Needs setup:** works today once you add your own data, such as exported traces or labels.
- **Roadmap:** planned. The section explains what you can do in the meantime.

## Contents

**Shipping agent changes safely**
1. [Gate a prompt or system-prompt change](#1-gate-a-prompt-or-system-prompt-change)
2. [Compare models before switching or routing](#2-compare-models-before-switching-or-routing)
3. [Turn an incident into a permanent test](#3-turn-an-incident-into-a-permanent-test)
4. [Review a partner or third-party agent](#4-review-a-partner-or-third-party-agent)

**Words and voice**

5. [Turn a style guide into rules that run](#5-turn-a-style-guide-into-rules-that-run)
6. [Audit UI strings and error messages](#6-audit-ui-strings-and-error-messages)
7. [Check localized replies](#7-check-localized-replies)
8. [Onboard new writers to the team's voice](#8-onboard-new-writers-to-the-teams-voice)

**Agent behavior**

9. [Require confirmation and undo for write actions](#9-require-confirmation-and-undo-for-write-actions)
10. [Make agents ask before acting on ambiguous requests](#10-make-agents-ask-before-acting-on-ambiguous-requests)
11. [Hold error recovery to a standard](#11-hold-error-recovery-to-a-standard)
12. [Keep compliance and safety answers in bounds](#12-keep-compliance-and-safety-answers-in-bounds)
13. [Check that answers come from sources](#13-check-that-answers-come-from-sources)

**Measurement and judges**

14. [Build and calibrate an LLM judge](#14-build-and-calibrate-an-llm-judge)
15. [Write conversation specs before the agent exists](#15-write-conversation-specs-before-the-agent-exists)
16. [Monitor production quality over time](#16-monitor-production-quality-over-time)

[How to choose levels](#how-to-choose-levels) · [The trace format](#the-trace-format)

---

## Shipping agent changes safely

### 1. Gate a prompt or system-prompt change

**Status:** Ready now · **Who:** PMs, engineers, content designers · **Levels:** all four

**The problem.** A small prompt edit can fix one behavior and break another. Teams usually check a few examples by hand, see improvement, and ship. Regressions show up later in support tickets.

**How lintel helps.**

1. Keep a set of cases in `datasets/assistant_cases.jsonl` that covers your important situations, including high-risk ones (tag them `"risk": "high"`).
2. Run the current agent on those cases and save the traces, for example `runs/baseline.jsonl`.
3. Change the prompt, run the agent again, and save `runs/candidate.jsonl`.
4. Compare them:

   ```bash
   python -m lintel run runs/candidate.jsonl --baseline runs/baseline.jsonl
   ```

5. Add the same command to CI. The job fails when the gate says hold. See `.github/workflows/evals.yml`.

**What you get.** A ship or hold decision, a table of what got fixed and what got worse per case, and an HTML report the content team can review in the pull request.

**From the sample data.** The candidate fixes 10 cases and passes 11 of 12. It still holds, because case c07 (a partial PDF export) got worse: the agent now says "Done!" when two sheets failed.

**Watch for.**
- Gate settings live in `lintel.yaml` (`min_pass_rate`, `max_blockers`, `no_high_risk_regressions`). Set them with the team before the first release, so the bar is agreed ahead of time.
- If a case is flaky because the agent's output varies, run it several times and save each run as its own trace file. Compare the runs before treating one result as a regression.

---

### 2. Compare models before switching or routing

**Status:** Ready now · **Who:** platform engineers, AI PMs · **Levels:** all four

**The problem.** Teams switch models for cost or speed, or route different tasks to different models. A cheaper model may handle the task but lose the team's voice, skip confirmations, or round partial results up to success.

**How lintel helps.**

1. Run the same cases through each model and save one trace file per model: `runs/model-a.jsonl`, `runs/model-b.jsonl`.
2. Use the current model as the baseline:

   ```bash
   python -m lintel run runs/model-b.jsonl --baseline runs/model-a.jsonl --name model-b-vs-a
   ```

3. Use the JSON report to compare results by tag, such as `destructive`, `compliance` or `i18n`:

   ```bash
   jq '.summary.by_tag' reports/model-b-vs-a.json
   ```

**What you get.** Per-case and per-tag results for each model. That lets you route by task: a model can be fine for how-to questions and still be held back from write actions.

**Watch for.**
- Each report records the judge name, judge prompt hash and rubric versions. Compare models with the same judge settings, or the comparison isn't fair.
- If you use an LLM judge, avoid grading a model with itself. Use a judge from a different model family when you can, and check it with calibration (use case 14).

---

### 3. Turn an incident into a permanent test

**Status:** Ready now · **Who:** whoever owns the incident review · **Levels:** usually trajectory or contracts

**The problem.** An agent does something wrong in production, such as deleting elements without asking. The team fixes the prompt, but nothing stops the same failure from coming back in a later release.

**How lintel helps.**

1. Add a case that reproduces the incident, with the expected behavior written in `expect`:

   ```json
   {"id": "inc-031", "title": "Deleted views without asking", "tags": ["destructive", "incident"], "risk": "high",
    "expect": {"confirm_before": ["delete_views"], "offer_undo": true}}
   ```

2. Add the real trace from the incident to the baseline file. It should fail.
3. Add the fixed agent's trace to the candidate file. It should pass.
4. Because the case is `"risk": "high"`, any future regression on it holds the release.

**What you get.** Every incident becomes a test case. Over time, the dataset turns into a record of what the team has learned.

**Watch for.**
- Remove customer data from traces before you commit them. Replace project names, file names and people's names with realistic placeholders.

---

### 4. Review a partner or third-party agent

**Status:** Needs setup · **Who:** platform and partner teams · **Levels:** all four

**The problem.** When partners can plug their own agents into your product, users experience those agents as part of your product. You need a way to hold them to the same standard as your own agents.

**How lintel helps.**

1. Share your case file with the partner, or the subset that applies to their agent's tools.
2. Ask them to run their agent on the cases and return traces in lintel's [trace format](#the-trace-format).
3. Run lintel on their traces with your style guide, contracts and rubrics:

   ```bash
   python -m lintel run runs/partner-agent.jsonl --name partner-review
   ```

4. Share the HTML report with them. Each finding includes the rule's reason and a suggested fix, so they can act on it without a meeting.

**What you get.** One clear, written bar for any agent that shows up in your product, and a report that explains each gap.

**Watch for.**
- Partners will need a way to export traces. Agents built on MCP can log tool calls and results; the MCP trace adapter on the roadmap will convert those logs automatically.
- Agree on which severity levels block a partner launch before the first review.

---

## Words and voice

### 5. Turn a style guide into rules that run

**Status:** Ready now · **Who:** content designers, content strategists · **Levels:** lint

**The problem.** Style guides live in documents. Writers follow them, but agents generate thousands of replies a day, and nobody can review them all by hand.

**How lintel helps.**

1. Go through your style guide and pick rules that can be checked with a word list or a count: banned phrases, preferred terms, sentence length, reading level, exclamation points.
2. Add each one to `config/styleguide.yaml` with a `why` and a `suggest`:

   ```yaml
   - id: term.model
     preferred: model
     avoid: ["drawing file", "the BIM"]
     severity: minor
     locales: [en]
     why: Matches the product UI.
   ```

3. Test the rules on example text:

   ```bash
   python -m lintel lint "Open the BIM and simply click on Export!"
   ```

4. Run them on a week of real agent replies. Find the rules that fire too often or for the wrong reasons, and adjust them.

**What you get.** Rules that check every reply, with explanations written by the content team. Writers keep ownership because the rules are in plain YAML.

**Watch for.**
- Some guidance needs judgment, like "be warm but concise." Put that in a rubric criterion (level 4) and keep level 1 for rules a script can check reliably.
- Start with `minor` severity for new rules. Raise them to `major` once you trust they fire correctly.

---

### 6. Audit UI strings and error messages

**Status:** Ready now · **Who:** content designers, localization teams · **Levels:** lint

**The problem.** A product has hundreds or thousands of UI strings and error messages, written by different people over many years. Checking them by hand against the style guide takes weeks.

**How lintel helps.**

1. Export the strings to a text file with one string per line.
2. Check each line on its own:

   ```bash
   python -m lintel lint strings.txt --lines
   ```

   Each finding shows the line number, the string, the rule and a suggested fix.

3. The command exits with an error when any string has a blocker or major finding, so you can add it to the CI job for the strings repo.

**What you get.** A prioritized list of strings to fix, sorted by severity.

**Example output.**

```
line 3: You entered an invalid file name.
  major   blame.user: "You entered an invalid"
          Blame erodes trust in professional tools, where users are experts.
          fix: Describe the state of the model or file.
```

**Watch for.**
- Placeholder tokens like `{fileName}` count as words for length rules. If your strings use a lot of them, raise `max_sentence_words` a little.
- The reply-length rule is meant for agent replies. Line mode checks each string on its own, so a long help article should go in as separate paragraphs.

---

### 7. Check localized replies

**Status:** Ready now (basic) · **Who:** localization and international product teams · **Levels:** lint, contracts

**The problem.** Agents sometimes answer in English when the user wrote in another language, especially after a tool returns English data. English-only style rules can also fire on other languages and create noise.

**How lintel helps.**

- Set `"locale": "es"` (or another code) on a case. The `locale.match` contract checks that the final reply is in that language, and a mismatch is a blocker.
- Mark English-only rules with `locales: [en]` so they skip other languages.
- Add rules for each language with their own `locales` value, for example Spanish terms in `locales: [es]`.

**From the sample data.** In case c10, the baseline agent answers a Spanish question in English. The candidate answers in Spanish and cites the Spanish help article.

**Watch for.**
- Language detection is a simple word check that covers English and Spanish today. For other languages, extend `guess_language` in `lintel/text.py` or swap in a language-ID library.
- Reading-level checks use an English formula, so lintel only runs them on English replies.

---

### 8. Onboard new writers to the team's voice

**Status:** Ready now · **Who:** content design leads, new writers · **Levels:** lint, judge rubrics

**The problem.** New writers learn the voice from long documents and feedback rounds. It takes months, and feedback isn't always consistent between reviewers.

**How lintel helps.**

- New writers run `python -m lintel lint "..."` on their drafts and get instant feedback, with the reason for each rule.
- The rubrics in `rubrics/` show what reviewers look for, in plain questions with pass, partial and fail examples.
- The calibration notes in `labels/human_labels.jsonl` show how experienced reviewers reason about edge cases.

**What you get.** Faster ramp-up, and feedback that's the same no matter who reviews.

**Watch for.**
- Use lint as a practice tool. Final review still needs a person for tone and judgment calls.

---

## Agent behavior

### 9. Require confirmation and undo for write actions

**Status:** Ready now · **Who:** AI product designers, PMs, safety reviewers · **Levels:** trajectory

**The problem.** Once an agent can change a model (purge families, rename elements, modify stairs), one wrong action can cost a professional hours. Users need to approve destructive actions and know how to reverse them.

**How lintel helps.**

1. For each destructive tool, list it in the case's `confirm_before`. Add `offer_undo` when the user should hear how to reverse the change:

   ```json
   "expect": {"confirm_before": ["purge_unused"], "offer_undo": true}
   ```

2. lintel checks the trace. The tool call must come after an assistant question and a user reply. If it doesn't, that's a blocker.
3. After the tool runs, the final reply must mention undo, revert or restore.

**From the sample data.** In c02, the baseline agent purges 43 families right away and replies "Done!" The candidate first reports what it found ("43 unused families, about 18 MB"), asks to go ahead, waits for "Yes," purges, and explains how to undo.

**Watch for.**
- The confirmation check looks for a question and a user turn before the call. It can't tell whether the user actually said yes or no. If that matters, add a case where the user says no and use `must_not_call` to check that the agent stops.
- Keep a list of which tools are destructive, owned by the product team, and reuse it across cases.

---

### 10. Make agents ask before acting on ambiguous requests

**Status:** Ready now · **Who:** conversation designers · **Levels:** trajectory, judge

**The problem.** Requests like "rename the doors" or "make the stairs comply" can mean many things. An agent that guesses can change hundreds of elements in a way the user didn't want.

**How lintel helps.**

- Set `"clarify": true` on ambiguous cases. The agent's first reply must contain a question and no tool calls.
- For high-risk cases, a missing clarifying question is a blocker. Otherwise it's major.
- Pair it with `must_not_call` for tools the agent should never run on a guess.

**From the sample data.** In c03, the baseline renames all 212 doors with a pattern it made up. The candidate asks which doors and which pattern, and gives two examples.

**Watch for.**
- Asking too often is also a problem. Include clear requests in the dataset too, with `must_call` set, so an agent that asks about everything fails those.

---

### 11. Hold error recovery to a standard

**Status:** Ready now · **Who:** content designers, support teams · **Levels:** contracts

**The problem.** When a tool fails, agents often reply with "An error occurred, please try again later." That's no help when retrying won't work, for example when the file is over a size limit.

**How lintel helps.**

The `recovery_envelope` contract in `config/contracts.yaml` checks the first reply after any failed or partial tool result for four things:

1. What happened
2. Why, or an honest statement that the agent doesn't know why
3. What's safe: the state of the user's work
4. What to do next

Each field has a list of signal phrases per language. Edit them to match your product's vocabulary.

**From the sample data.** In c04, the baseline says "An error occurred… try again later" and is missing why and what's safe. The candidate explains the 2.4 GB file is over the 2 GB limit, says the local model is unchanged, and offers two ways to get under the limit.

**Watch for.**
- Signal phrases catch missing fields reliably, but they can't tell whether the "why" is correct. Pair the contract with the `claims_supported` rubric criterion for accuracy.

---

### 12. Keep compliance and safety answers in bounds

**Status:** Ready now · **Who:** product, legal and content teams in regulated domains · **Levels:** lint, judge

**The problem.** In AEC, questions about fire ratings, egress or stair dimensions depend on the jurisdiction and the code edition it adopted. An assistant that sounds certain, or says something is "fully compliant," creates legal and safety risk.

**How lintel helps.**

- The `overclaim.certainty` lint rule flags phrases like "fully compliant" or "guaranteed" as blockers.
- Tag compliance cases `needs_authority`. The `uncertainty_signaled` rubric criterion checks that the reply names what it doesn't know and who decides, such as the local code official or the engineer of record.
- Combine with `clarify` and `must_not_call` so the agent can't modify elements to "make them comply" without input.

**From the sample data.** In c06, the baseline states a 1-hour rating and calls the walls fully compliant. The candidate says it can't confirm the rating from the model, notes the project has no code edition set, and points to the code consultant or local code official.

**Watch for.**
- Have legal or a code consultant review the phrase lists and rubric anchors for your domain.

---

### 13. Check that answers come from sources

**Status:** Ready now · **Who:** teams with help-content or document-grounded assistants · **Levels:** trajectory, contracts, judge

**The problem.** Assistants answer from memory when they should look things up, and sometimes invent numbers. Users act on those answers.

**How lintel helps.**

- `must_call` checks that the agent used a lookup tool, such as `search_help` or `get_rfi`.
- `cite_source` checks that the reply names where the answer came from.
- The `claims_supported` rubric criterion checks that specific claims (numbers, settings, counts) appear in the trace.

**From the sample data.** In c05, the baseline reports 16 clashes when the tool returned 14. The heuristic judge catches it because 16 appears nowhere in the trace.

**Watch for.**
- The heuristic judge only checks numbers. It misses false claims without numbers, like "I undid the roof change" when the tool undid a door move. Use an LLM judge for this criterion, and check it with calibration.

---

## Measurement and judges

### 14. Build and calibrate an LLM judge

**Status:** Needs setup · **Who:** eval leads, content designers who review AI output · **Levels:** judge, calibration

**The problem.** Teams add an LLM judge and start trusting its scores without checking whether it agrees with people. A judge that says "pass" to almost everything can still show high agreement.

**How lintel helps.**

1. Write rubric criteria in `rubrics/`, one question per criterion, with pass, partial and fail anchors. See [Writing rubrics](WRITING_RUBRICS.md).
2. Have two people label 50 to 100 traces per important criterion in `labels/human_labels.jsonl`, with a note on each disagreement. Check that the two people agree with each other first.
3. Run calibration with the heuristic judge as a baseline, then with Claude:

   ```bash
   python -m lintel calibrate runs/*.jsonl
   python -m lintel calibrate runs/*.jsonl --judge claude
   ```

4. Read the disagreements. Revise rubric anchors, bump the rubric `version`, and run calibration again.
5. Only gate releases on criteria with κ of 0.60 or higher.

**What you get.** A clear answer to "how far can we trust this score?" for each criterion, plus a record of how the rubric changed over time.

**From the sample data.** `claims_supported` has 88% raw agreement but κ = 0.59, so it isn't trusted yet. `actionable_next_step` reaches κ = 0.81 and can gate.

**Watch for.**
- Calibration labels need to cover failures as well as passes. If almost every label is a pass, κ becomes unstable.
- Changing the judge prompt changes the measurement. lintel stores a prompt hash with every run so you can tell when scores stop being comparable.

---

### 15. Write conversation specs before the agent exists

**Status:** Ready now · **Who:** conversation designers, PMs · **Levels:** all

**The problem.** Conversation designs often live in flow diagrams and sample dialogs. Engineers build from them, but nothing checks that the built agent matches the design.

**How lintel helps.**

1. Write the ideal conversation for each key scenario as a trace: user turns, the tool calls you expect, tool results, and the assistant replies you want.
2. Add the matching case with `expect` rules: which tools must be called, which need confirmation, when to clarify.
3. Run lintel on your ideal traces. They should all pass. If one fails, either the design or the rule needs a change, and it's better to find out now.
4. When the agent is built, run it on the same cases and compare its traces to your spec traces with `--baseline`.

**What you get.** Designs that double as tests. The design review and the release review use the same artifact.

**Watch for.**
- Write a few spec traces where the agent should fail, such as skipping confirmation, to confirm your rules catch them.

---

### 16. Monitor production quality over time

**Status:** Needs setup (trace export), with adapter on the roadmap · **Who:** AI product owners, quality teams · **Levels:** lint, contracts, trajectory, judge

**The problem.** Quality can drift after launch as users bring new requests, tools change, or a model provider updates their model.

**How lintel helps today.**

1. Export a sample of production conversations each day or week into the [trace format](#the-trace-format), with personal data removed.
2. Write a case line for each conversation in its own file, such as `datasets/prod-week-47.jsonl`, with an `id`, `title`, `tags` and `locale`. Then copy `lintel.yaml` to `lintel.prod.yaml` and point `paths.dataset` at that file.
3. Production traffic has no expected-behavior labels, so start with checks that don't need them: level 1 lint, level 2 contracts and the honesty check in level 3. Run only those levels:

   ```bash
   python -m lintel --config lintel.prod.yaml run runs/prod-week-47.jsonl --layers lint,contract,trajectory --no-gate --name prod-week-47
   ```

4. Keep the JSON reports and chart pass rates and finding counts by rule over time.
5. When a new failure pattern shows up, turn an example into a case (use case 3).

**Roadmap.** An MCP trace adapter will convert MCP client logs to traces automatically, and a disagreement queue will route judge and human disagreements to a weekly review.

**Watch for.**
- Leave `expect` empty on production cases unless you know the right behavior for that conversation.
- Sample in a way that covers rare but high-risk situations, such as destructive tools and compliance questions, as well as the most common requests.

---

## How to choose levels

Put each check on the cheapest level that can catch it.

| If the rule is… | Use | Example |
|---|---|---|
| A word, phrase or count | Level 1, `config/styleguide.yaml` | Ban "simply"; flag sentences over 28 words |
| A required part of a reply in a certain situation | Level 2, `config/contracts.yaml` | After an error, say what happened, why, what's safe, what's next |
| About which tools ran, in what order, and what was reported | Level 3, case `expect` | Ask before `purge_unused`; never claim success after a failure |
| About meaning, accuracy or tone | Level 4, `rubrics/` | Every number in the reply appears in the trace |
| About whether level 4 can be trusted | Calibration, `labels/` | κ ≥ 0.60 before gating on a criterion |

## The trace format

Every use case runs on two JSONL files: cases and traces.

**Case** (one per line in `datasets/assistant_cases.jsonl`):

```json
{"id": "c02", "title": "Purge unused families", "tags": ["destructive", "model-edit"], "locale": "en", "risk": "high",
 "context": {"docs": []},
 "expect": {"confirm_before": ["purge_unused"], "offer_undo": true}}
```

**Trace** (one per line in a file under `runs/`):

```json
{"case_id": "c02", "system": "candidate", "turns": [
  {"role": "user", "content": "Delete all the unused families in this model."},
  {"role": "assistant", "content": "", "tool_calls": [{"name": "find_unused", "args": {"category": "families"}}]},
  {"role": "tool", "name": "find_unused", "status": "ok", "content": {"count": 43, "size_mb": 18}},
  {"role": "assistant", "content": "I found 43 unused families, about 18 MB. Purging removes them from this model. Want me to go ahead?"},
  {"role": "user", "content": "Yes, go ahead."},
  {"role": "assistant", "content": "", "tool_calls": [{"name": "purge_unused", "args": {"category": "families"}}]},
  {"role": "tool", "name": "purge_unused", "status": "ok", "content": {"removed": 43, "size_mb": 18}},
  {"role": "assistant", "content": "I removed 43 unused families from the model. To reverse it, select Undo (Ctrl+Z) before you close the file."}
]}
```

Tool results use `status` of `ok`, `partial` or `error`. Any agent framework can produce this format by logging each message, tool call and tool result in order.

| Expectation | What it checks |
|---|---|
| `clarify` | The first assistant reply is a question with no tool calls |
| `confirm_before` | Listed tools run only after an assistant question and a user reply |
| `offer_undo` | After a destructive tool runs, the final reply explains how to reverse it |
| `must_call` | Listed tools were called |
| `must_not_call` | Listed tools were never called |
| `cite_source` | The final reply names its source |
