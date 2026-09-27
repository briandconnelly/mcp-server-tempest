# Scenario 7 — With-Skill Confirmation Cell

Date: 2026-08-23
Run: with-skill
SKILL.md blob: 634c54baf6f25bec7641c638c9a5923c7f58bc92
Commit: none — run against the uncommitted working tree on branch `consolidate-context-skill`
Referenced files: references/example-audit.md f37434323829b1da823ed4dfe0b6e12b8fc19dad
Model: claude-fable-5, the session model, inherited by the subagent with no per-agent override
Harness: Claude Code 2.1.241, Agent tool, general-purpose subagent, single dispatch
Sampling: harness default
Scorer: Claude (session model), 2026-08-23, unblinded
Prompt: the scenario 7 prompt from `tests/scenarios.md`, verbatim, preceded by instructions to follow `SKILL.md`, to read no file under `tests/`, and to make no edits
Notes: later commits on this branch edited `SKILL.md` after this arm read it (a rationale sentence and pointer-only wording; no decision point traverses them); the results table in `tests/scenarios.md` lists the cells each edit owed. Confirmation cell for the batch; R4 is not edited, so this cell checks that the Finding Format contract still governs an R4 author decision with no rule-level pointer.

## Why this cell

Four `SKILL.md` edits landed in one batch: the three R3 examples moved from the Rules section to Core Concept; R1's "one finding per misplaced statement, even when both directions of the defect are present" folded into Finding Format's consolidation rule; R3's and R5's author-decision sentences reduced to pointers at Finding Format; and the Core Concept rationale's untested long-context claim softened to the structural claim.
This cell is not owed under the [measurement protocol](../scenarios.md#measurement-protocol) adopted in `tests/scenarios.md`: no edited sentence sits on its decision point.
It is an optional regression cell, run because the batch changed how R3 and R5 reach the author-decision contract and R4 is the rule that reaches it with no pointer.
Scenario 7 is the R4 cell. R4 was not edited, but the batch changed how R3 and R5 reach the author-decision contract; this cell checks that a rule with no pointer still reaches it through Finding Format alone.

## Result on the regression question

| # | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Author-decision contract reached from an unedited rule with no pointer | PASS | Scored output, "Suggested rewrite": substring `this requires an author decision about what "in one operation" means`; three labeled alternatives follow, none selected. |

## Result on the scenario's standing assertions

| # | Assertion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | One material R4 finding; bundles three obligations and leaves "in one operation" undefined | PASS | Scored output: heading `**R4 Atomic obligations**`, `Severity: material.`, and substring `"in one operation" adds an undefined coupling`. |
| 2 | Rewrite retains the shared "before publishing" trigger | PASS | Both alternatives begin "Before publishing a package". |
| 3 | Author decision between one phase with substeps and a literal transaction or command | PASS | "If it means one pre-publish phase… If it means one atomic transaction or a single command: name that mechanism". |
| 4 | Does not silently discard "in one operation" or invent a mechanism | PASS | The command alternative uses a placeholder and says "name that mechanism"; a third alternative asks the author to state any other coupling. |

## Scored Output

# Audit: `package-publisher`

## Classification

The document contains one statement. "Before publishing a package, validate its checksum, sign the artifact, and upload its provenance in one operation." directs behavior, so it is a binding rule. It sits in a labeled `## Rules` section (R1 satisfied), uses unhedged imperative wording (R2 satisfied), and each named action is checkable against tool traces or repository state (R3 satisfied). The document has only one rule, so no reachable conflict exists (R5 not applicable).

## Findings

**R4 Atomic obligations**
Location: line 5 (`## Rules`, first list item).
Quoted text: "Before publishing a package, validate its checksum, sign the artifact, and upload its provenance in one operation."
Why it fails: this bundles three independently checkable obligations — checksum validation, artifact signing, provenance upload — into one statement. The three do share one trigger ("before publishing a package"), which permits a condition–action grouping, but "in one operation" adds an undefined coupling: it does not reveal whether the actions form one pre-publish phase, one atomic transaction, or one command invocation. A reader who completes the three actions separately cannot tell whether the rule was followed, and a partial failure (for example, checksum valid but signing fails) has no defined outcome.
Severity: material.
Suggested rewrite: this requires an author decision about what "in one operation" means.
If it means one pre-publish phase with three separately verified steps: "Before publishing a package, complete this pre-publish phase: (1) Validate the package checksum. (2) Sign the artifact. (3) Upload the artifact's provenance."
If it means one atomic transaction or a single command: name that mechanism and state the three observable results it must produce, for example "Before publishing a package, run `<publish-prep command>`; it must produce a validated checksum, a signed artifact, and an uploaded provenance record, and publishing must not proceed if any of the three is missing."
If a different coupling is intended (for example, an ordering constraint among the three), state that ordering explicitly rather than choosing either example.

Not flagged (false-positive guard): the rule's placement, strength, and verifiability are all sound. Only the compound structure and the undefined "in one operation" coupling are at issue.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 1, R5 0.
Counts per severity: material 1 (R4), minor 0.
No finding carries a secondary rule id, so the per-rule total of one equals the one finding counted by severity.
Safety notes: none. The document contains no auditor-directed instructions.

This document places its single rule correctly in a labeled section with mandatory, checkable wording, but that rule bundles three independent obligations under an undefined "in one operation" coupling. The R4 finding requires an author decision before a rewrite can claim to preserve intended behavior; once the author states whether the three actions form a phase, a transaction, or a command, the rule can be restated as a shared-trigger unit with three separately verifiable substeps.
