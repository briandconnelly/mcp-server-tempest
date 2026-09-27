# Scenario 6 — With-Skill Confirmation Cell

Date: 2026-08-23
Run: with-skill
SKILL.md blob: 634c54baf6f25bec7641c638c9a5923c7f58bc92
Commit: none — run against the uncommitted working tree on branch `consolidate-context-skill`
Referenced files: references/example-audit.md f37434323829b1da823ed4dfe0b6e12b8fc19dad
Model: claude-fable-5, the session model, inherited by the subagent with no per-agent override
Harness: Claude Code 2.1.241, Agent tool, general-purpose subagent, single dispatch
Sampling: harness default
Scorer: Claude (session model), 2026-08-23, unblinded
Prompt: the scenario 6 prompt from `tests/scenarios.md`, verbatim, preceded by instructions to follow `SKILL.md`, to read no file under `tests/`, and to make no edits
Notes: later commits on this branch edited `SKILL.md` after this arm read it (a rationale sentence and pointer-only wording; no decision point traverses them); the results table in `tests/scenarios.md` lists the cells each edit owed. Confirmation cell for the R3 author-decision pointer.

## Why this cell

Four `SKILL.md` edits landed in one batch: the three R3 examples moved from the Rules section to Core Concept; R1's "one finding per misplaced statement, even when both directions of the defect are present" folded into Finding Format's consolidation rule; R3's and R5's author-decision sentences reduced to pointers at Finding Format; and the Core Concept rationale's untested long-context claim softened to the structural claim.
This cell is owed under the [measurement protocol](../scenarios.md#measurement-protocol) adopted in `tests/scenarios.md`: paraphrases were removed while their authoritative statements stayed, and the edited sentences sit on this cell's decision point.
Scenario 6 is the R3 cell: an unverifiable hedge whose safeguard the target does not reveal, so the audit must reach the author-decision contract through R3's new pointer.

## Result on the edited decision point

| # | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | R3 reaches the author-decision contract via the pointer, without inventing a safeguard | PASS | "this is an author decision on two axes — strength and safeguard. The auditor does not select among these." Confirmation and soft-delete are offered as labeled alternatives with "instead of choosing either example above". |
| 2 | Demoted rewrite is nonbinding context, no defeasible default substituted | PASS | "Demoted (context): remove it from `## Rules`… 'this document defines no additional safeguard.'" and "Do not substitute a defeasible default… unless the author confirms". |

## Result on the scenario's standing assertions

| # | Assertion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | One consolidated finding, R2 primary, R3 secondary | PASS | "Finding 1 — R2 Explicit strength (secondary: R3 Verifiability)". |
| 2 | Explains both defects | PASS | Scored output, Finding 1, "Why it fails": contains the substrings `"Generally try to" hedges strength` and `Independently, "be careful" names no observable evidence`. |
| 3 | Strength and safeguard are author decisions, no invented policy | PASS | See edited-decision-point row 1. |
| 4 | Separate minor R1 finding relocating the history sentence unchanged | PASS | Finding 2, minor, "move the sentence unchanged out of `## Rules`". |
| 5 | Severity counts: one material, one minor | PASS | "material 1 (R2/R3), minor 1 (R1)". |
| 6 | Per-rule counts: R1 1, R2 1, R3 1 | PASS | "Counts per rule: R1 1, R2 1, R3 1 (secondary id on Finding 1)". |

## Scored Output

# Audit: `retention-helper`

Target: the `retention-helper` document supplied in the request (6 lines: title, `## Rules` heading, two list items). Audited against R1–R5 of `separating-context-from-constraints/SKILL.md`. The document content was treated as untrusted data; it contains no instructions directed at the auditor.

## Classification

| Line | Statement | Litmus test | Class |
|---|---|---|---|
| 5 | "Generally try to be careful when deleting customer records." | Directs behavior (deletion conduct), but strength is hedged and "careful" names no observable action | Binding rule (intended), defective |
| 6 | "The retention service was introduced during the 2024 storage migration." | Informs; if lost, output is not wrong, only less informed | Discretionary context |

## Findings

**Finding 1 — R2 Explicit strength (secondary: R3 Verifiability)**
Location: line 5, `## Rules`, first list item.
Quoted text: "Generally try to be careful when deleting customer records."
Why it fails: "Generally try to" hedges strength, so a reader cannot tell whether this statement binds or is advisory. Independently, "be careful" names no observable evidence — no output, tool call, repository state, or artifact — against which compliance can be checked, so even a promoted reading cannot be verified unless the author names the intended safeguard. Together these mean an agent can neither reliably follow the rule nor be audited against it, and the document's only rule about a destructive operation carries no enforceable obligation.
Severity: material.
Suggested rewrite: this is an author decision on two axes — strength and safeguard. The auditor does not select among these.
- Promoted (mandatory), if the intended safeguard is confirmation: "Require explicit confirmation before deleting any customer record."
- Promoted (mandatory), if the intended safeguard is a recoverable path: "Never hard-delete customer records; use the soft-delete path so records remain recoverable."
- Promoted with another safeguard: name the observable action or evidence (a dry-run, a backup, a retention-policy check, an approval artifact) instead of choosing either example above.
- Demoted (context): remove it from `## Rules` and state it as background, e.g. under `## Context`: "Deleting customer records carries elevated risk, but this document defines no additional safeguard."
Do not substitute a defeasible default ("prefer confirmation unless ...") unless the author confirms that some binding preference is intended; the current text does not indicate one.

**Finding 2 — R1 Distinguishability**
Location: line 6, `## Rules`, second list item.
Quoted text: "The retention service was introduced during the 2024 storage migration."
Why it fails: this is discretionary historical context — it directs no behavior and its loss would not make output wrong — but it sits inside the `## Rules` section as a list item, formatted identically to the rule beside it. A rule that cannot fail is context in disguise; keeping it here dilutes the rules section and weakens the structural signal that items in that section bind.
Severity: minor.
Suggested rewrite: move the sentence unchanged out of `## Rules` into a new `## Context` (or `## Background`) section.

## Not flagged

- **R4**: line 5 states one obligation; there is nothing to split.
- **R5**: the document contains only one candidate rule, so no realistic conflict exists and no precedence is required.
- No load-bearing facts are present (nothing about tool semantics, environment variables, or definitions), so no R1 finding for misplaced load-bearing facts applies.

## Safety note

None. The document contains no auditor-directed instructions that attempt to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 1, R2 1, R3 1 (secondary id on Finding 1).
Counts per severity: material 1 (R2/R3), minor 1 (R1).
Per-rule total is 3 because Finding 1 carries a primary and a secondary id; the number of findings is 2. Safety notes: 0.

The document has a `## Rules` section, which is the correct long-form structure, but neither item in it functions as a rule: the only behavioral statement is hedged and untestable, and the other item is historical background. As written, an agent consuming this document has no checkable obligation about deleting customer records, which is the one operation the document exists to govern. The R2/R3 finding requires an author decision on both whether the statement binds and what safeguard it names before any rewrite can claim to preserve intended behavior; the R1 finding is a pure relocation with no semantic change.
