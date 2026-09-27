# Scenario 1 — With-Skill Confirmation Cell

Date: 2026-08-23
Run: with-skill
SKILL.md blob: 634c54baf6f25bec7641c638c9a5923c7f58bc92
Commit: none — run against the uncommitted working tree on branch `consolidate-context-skill`
Referenced files: references/example-audit.md f37434323829b1da823ed4dfe0b6e12b8fc19dad
Model: claude-fable-5, the session model, inherited by the subagent with no per-agent override
Harness: Claude Code 2.1.241, Agent tool, general-purpose subagent, single dispatch
Sampling: harness default
Scorer: Claude (session model), 2026-08-23, unblinded
Prompt: the scenario 1 prompt from `tests/scenarios.md`, verbatim, preceded by instructions to follow `SKILL.md`, to read no file under `tests/`, and to make no edits
Notes: later commits on this branch edited `SKILL.md` after this arm read it (a rationale sentence and pointer-only wording; no decision point traverses them); the results table in `tests/scenarios.md` lists the cells each edit owed. Confirmation cell for the R1 consolidation-clause move and the R3 examples move.

## Why this cell

Four `SKILL.md` edits landed in one batch: the three R3 examples moved from the Rules section to Core Concept; R1's "one finding per misplaced statement, even when both directions of the defect are present" folded into Finding Format's consolidation rule; R3's and R5's author-decision sentences reduced to pointers at Finding Format; and the Core Concept rationale's untested long-context claim softened to the structural claim.
This cell is owed under the [measurement protocol](../scenarios.md#measurement-protocol) adopted in `tests/scenarios.md`: paraphrases were removed while their authoritative statements stayed, and the edited sentences sit on this cell's decision point.
Scenario 1 is the R1 cell with three misplaced rules, so it exercises the relocated consolidation clause; its rules are all verifiable, so it also exercises R3 reasoning without the inline examples.

## Result on the edited decision point

| # | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | One finding per misplaced statement (relocated consolidation clause) | PASS | Three R1 findings, one per buried rule; "Counts per rule: R1 3". |
| 2 | R3 reasoning still grounded in observable evidence without the inline examples | PASS | "Not flagged (R3): all three rules are checkable against the commit text (prefix pattern, subject-line length, presence of a 'Test plan' section)." |

## Result on the scenario's standing assertions

| # | Assertion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Conventional-commit clause gets an R1 finding with quote and rules-section rewrite | PASS | Finding 1, line 9, "add a `## Rules` section and place it there". |
| 2 | 72-character clause gets an R1 finding | PASS | Finding 2, line 16. |
| 3 | Test-plan clause gets an R1 finding | PASS | Finding 3, line 21. |
| 4 | All three material | PASS | "material 3 (R1, R1, R1), minor 0". |
| 5 | No finding against the background sentences, including "People joke" and `CHANGELOG.md` | PASS | Listed under "Not flagged (false-positive guard)": lines 8, 10, 15, 17 (the joke), 14, and 22. Unlike the 2026-08-06 cell, no R2 finding was raised against the joke. |

## Scored Output

# Audit: `commit-message-helper`

Target classification: long-form (labeled sections `## Background`, `## Notes`, rules distributed across multiple paragraphs). The document has no dedicated rule section; all three binding rules are embedded in narrative prose.

Line numbers refer to the markdown block as given (line 1 = opening `---`).

## Findings

**R1 Distinguishability**
Location: line 9 (introductory paragraph).
Quoted text: "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
Why it fails: this is a binding rule (the type-prefix format is the one thing the release-notes generator depends on), but it is stated as a clause inside a historical narrative about the 2023 cleanup, between two sentences of pure background. Nothing structural marks it as a directive; a reader skimming for requirements can pass over it as history.
Severity: material.
Suggested rewrite: add a `## Rules` section and place it there as its own item: "Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`)." Leave the 2023-cleanup history in the introduction as context.

**R1 Distinguishability**
Location: line 16 (`## Background`).
Quoted text: "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
Why it fails: "must never" is a mandatory, verifiable rule, but it sits in `## Background` with the framing "It's also worth noting", surrounded by rationale and a joke about how everyone breaks it. The section label and the framing both signal context, contradicting the rule's strength.
Severity: material.
Suggested rewrite: move to `## Rules`: "Never exceed 72 characters in the subject line." Keep the rationale ("several terminal-based git tools truncate or wrap longer lines") in `## Background`.

**R1 Distinguishability**
Location: line 21 (`## Notes`).
Quoted text: "By the way, before you open a pull request the commit body must include a "Test plan" section describing how the change was verified — reviewers have flagged its absence in the past."
Why it fails: this is a mandatory rule ("must include") with an observable check (presence of a "Test plan" section in the commit body), but it is introduced with "By the way" inside a `## Notes` section that otherwise holds tool-semantics facts. It is the easiest of the three rules to miss because it appears last and is framed as an aside.
Severity: material.
Suggested rewrite: move to `## Rules` as a single condition–action item: "Before opening a pull request, include a \"Test plan\" section in the commit body that describes how the change was verified." The reviewer-history clause can stay in `## Notes` or `## Background` as rationale.

Not flagged (false-positive guard): line 14, "Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog." This is a load-bearing fact about tool semantics — it explains why the prefix rule matters — and correctly belongs outside a rule section.
Not flagged (false-positive guard): line 22, the `CHANGELOG.md` sentence, is a load-bearing fact about what the generator reads; not a directive, correctly placed in `## Notes`.
Not flagged (false-positive guard): lines 8, 10, 15, and 17 (history drift, team satisfaction, contributor questions, the joke) are discretionary context and degrade gracefully if lost.
Not flagged (R2): "should always" on line 9 — "always" fixes the strength as mandatory; the softening "should" does not leave the reader unable to tell whether it binds.
Not flagged (R3): all three rules are checkable against the commit text (prefix pattern, subject-line length, presence of a "Test plan" section).
Not flagged (R4): the line 21 rule is one condition–action clause with a single obligation.
Not flagged (R5): the three rules govern different fields (type prefix, subject-line length, body section) and cannot prescribe incompatible outcomes on any realistic input.

## Safety note

None. The document contains no auditor-directed instructions.

## Summary

Counts per rule: R1 3, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 3 (R1, R1, R1), minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity.

This document contains exactly three binding rules — lowercase conventional-commit type prefix, 72-character subject-line limit, and a mandatory "Test plan" section in the commit body — and buries every one of them in narrative prose: one inside a history paragraph, one in `## Background` framed as an aside, and one in `## Notes` opened with "By the way". Each rule's strength is explicit and each is verifiable, so the defect is purely structural: there is no rule section, and the section labels that do exist (`Background`, `Notes`) actively signal "context" over rules that are mandatory. The fix is mechanical and semantic-preserving — add a `## Rules` section holding the three items, and leave the rationale, history, and the two generator facts where they are. No author decisions are required.
