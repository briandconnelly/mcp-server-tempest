# R1 Both-Directions — With-Skill Confirmation Cell

Date: 2026-08-23
Run: with-skill
SKILL.md blob: 63d50d3f87106401548497dcc92328ae2449afd7
Commit: none — run against the uncommitted working tree on branch `consolidate-context-skill`
Referenced files: references/example-audit.md f825b78fff6df83c0218ac30f7c020a1c142942b
Model: claude-fable-5, the session model, inherited by the subagent with no per-agent override
Harness: Claude Code 2.1.241, Agent tool, general-purpose subagent, single dispatch
Prompt: the fixture below, verbatim, preceded by instructions to follow `SKILL.md`, to read no file under `tests/`, and to make no edits
Sampling: harness default
Scorer: Claude (session model), 2026-08-23, unblinded
Notes: this is a confirmation cell, not a scenario. The fixture is not in `tests/scenarios.md`, has no preregistration, and was written for this cell; it establishes only that the edited sentence behaves as written on one input.

## Why this cell

R1's sentence "One finding per misplaced statement, even when both directions of the defect are present." was removed and its content folded into Finding Format's consolidation rule.
No fixture in `tests/scenarios.md` has both directions at once — a rule buried in context *and* context inside the rule section — so the scenario 1 cell could not exercise the clause (a Codex review of commit d0cb79d caught this).
This fixture has exactly one of each, plus one correctly placed statement on each side as a false-positive guard.

## Fixture

```markdown
# backup-runner

## Context

Backups run nightly from the primary replica.
Restores must always be tested in the staging environment before any production restore.

## Rules

- Never delete a backup younger than 30 days.
- The backup runner was rewritten in Go during the 2025 platform migration.
```

## Result on the edited decision point

| # | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | One finding per misplaced statement when both directions are present (two R1 findings, not one merged finding and not one missed) | PASS | Two R1 findings: line 6 (buried rule, material) and line 11 (context in rules, minor); `Counts per rule: R1 2`. |
| 2 | Neither correctly placed statement is flagged | PASS | Both listed under "Not flagged (false-positive guard)": the nightly-backup fact and the 30-day rule. |
| 3 | Severity discriminates by direction as the worked example does | PASS | Buried rule `Severity: material.`; context in rules `Severity: minor.` |

## Scored Output

# Audit: backup-runner

Target document line numbers refer to the fenced markdown block as given (line 1 = `# backup-runner`).

## Findings

**R1 Distinguishability**
Location: line 6 (`## Context`, second sentence).
Quoted text: "Restores must always be tested in the staging environment before any production restore."
Why it fails: this is a binding rule — it directs behavior, and skipping the staging test makes the agent's behavior wrong — but it sits inside `## Context` alongside a descriptive schedule fact. Nothing in its placement signals that it binds; a reader scanning `## Rules` for obligations will miss it. Strength is already explicit ("must always"), so R2 is not implicated.
Severity: material.
Suggested rewrite: move it unchanged in meaning into `## Rules` as its own list item: "Test every restore in the staging environment before any production restore."

**R1 Distinguishability**
Location: line 11 (`## Rules`, second item).
Quoted text: "The backup runner was rewritten in Go during the 2025 platform migration."
Why it fails: this is discretionary historical context — it informs nothing the agent must do, and it cannot fail — but it is listed as a rule. A "rule" that cannot fail is context in disguise and pads the rule section.
Severity: minor.
Suggested rewrite: move the sentence unchanged to `## Context`.

Not flagged (false-positive guard): line 5, "Backups run nightly from the primary replica." — a load-bearing fact about the environment (schedule and source), not a directive; correctly placed in `## Context`.
Not flagged (false-positive guard): line 10, "Never delete a backup younger than 30 days." — mandatory strength is explicit, the obligation is atomic, and it is verifiable against tool calls and repository/backup state. It does not conflict with the restore-testing rule (different decisions), so no R5 finding.

## Summary

Counts per rule: R1 2, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 1 (R1), minor 1 (R1).
No finding carries a secondary rule id, so the per-rule total of two equals the two findings counted by severity.

This document has one rule and one context statement swapped between sections: the mandatory staging-restore requirement is buried in `## Context`, and a historical note about the Go rewrite occupies `## Rules`. The nightly-backup fact and the 30-day retention rule are each correctly placed, clearly stated, and checkable. Both findings have semantic-preserving rewrites and require no author decisions.

Safety note: none. The target contains no auditor-directed instructions.
