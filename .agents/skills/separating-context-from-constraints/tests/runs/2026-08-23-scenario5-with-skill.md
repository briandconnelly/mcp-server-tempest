# Scenario 5 — With-Skill Confirmation Cell

Date: 2026-08-23
Run: with-skill
SKILL.md blob: 6ac92794f7cd43b84c1011d3c69ee5beaa9d8667
Commit: none — run against the uncommitted working tree on branch `consolidate-context-skill`
Referenced files: references/example-audit.md f37434323829b1da823ed4dfe0b6e12b8fc19dad
Model: claude-fable-5, the session model, inherited by the subagent with no per-agent override
Harness: Claude Code 2.1.241, Agent tool, general-purpose subagent, single dispatch
Sampling: harness default
Scorer: Claude (session model), 2026-08-23, unblinded
Prompt: the scenario 5 prompt from `tests/scenarios.md`, verbatim, preceded by instructions to follow `SKILL.md`, to read no file under `tests/`, and to make no edits
Notes: Later commits on this branch edited `SKILL.md` after this arm read it; the results table in `tests/scenarios.md` lists the cells each of those edits owed and ran. Confirmation cell for the Non-Goals consolidation (numeric-scoring paraphrase removed); see "Why this cell" below.

## Why this cell

The Non-Goals bullet "Numeric scoring or pass/fail grading of documents" duplicated Summary Format's "Do not include a numeric score."
The bullet was reduced to "Pass/fail grading of documents (numeric scores are excluded by Summary Format)", leaving Summary Format as the only home.
This cell is owed under the [measurement protocol](../scenarios.md#measurement-protocol) adopted in `tests/scenarios.md`: a paraphrase was removed while its authoritative statement stayed.
Scenario 5 is the cell where a score is most tempting: a clean document with nothing else to report.

## Result on the edited decision point

| # | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | No numeric score or pass/fail grade in the output | PASS | Summary reports "Counts per rule: R1 0 … Counts per severity: material 0, minor 0." and a prose assessment; no score, grade, or percentage appears. |
| 2 | No cross-layer analysis | PASS | The report reasons only about the target's own sections. |

The consolidated Non-Goals wording works as written for this cell.

## Result on the scenario's standing assertions

| # | Assertion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Reports a clean outcome for R1–R5 | PASS | "Clean — no findings." |
| 2 | No manufactured minor findings against rules 1–5 or the context sentences | PASS | All classified and explicitly "Not flagged"; rule 7's redundant clause noted as out-of-scope prose, not a finding. |
| 3 | Does not flag rule 6's "by default" as an R2 hedge | PASS | "Rule 6 is an explicit default ('by default') whose override condition is stated in rule 7." |
| 4 | Does not raise an R5 finding | PASS | "rule 7 states explicitly that it takes precedence." |

## Scored Output

# Audit Report: `changelog-entry-writer`

## Classification

| Location | Statement | Class |
|---|---|---|
| Context, sentence 1 | "Changelog entries are read by users deciding whether to upgrade, not by contributors reviewing code." | Discretionary context (rationale for rules 2–5) |
| Context, sentence 2 | "This skill is invoked once per merged pull request, after CI has passed." | Load-bearing fact (invocation environment) |
| Rule 1 | Tag with exactly one of four tags | Binding rule (mandatory) |
| Rule 2 | User-visible effect in first sentence | Binding rule (mandatory) |
| Rule 3 | Never name function/class/variable | Binding rule (mandatory) |
| Rule 4 | Never reference internal ticket number | Binding rule (mandatory) |
| Rule 5 | Never reference file path | Binding rule (mandatory) |
| Rule 6 | One entry per PR by default | Binding rule (explicit default) |
| Rule 7 | One entry per change when PR bundles independent changes; takes precedence over rule 6 | Binding rule (mandatory exception with stated precedence) |

## Findings

Clean — no findings.

Rule-by-rule check:

- **R1 Distinguishability.** The document is long-form (labeled sections). All seven binding rules sit in the dedicated `## Rules` section as numbered items. The `## Context` section contains only the rationale sentence and the invocation fact; neither directs behavior, and both are correctly placed outside `## Rules`. No rule is buried in the context prose, and no context or fact is placed in the rules list. Every rule can fail (a wrong tag, a buried effect statement, a named identifier, a ticket reference, a file path, a wrong entry count), so none is context in disguise.
- **R2 Explicit strength.** Rules 1–5 and 7 use unhedged mandatory wording ("exactly one", "Never", "instead"). Rule 6 is an explicit default ("by default") whose override condition is stated in rule 7. No hedges ("generally", "try to") appear.
- **R3 Verifiability.** Each rule is checkable against the produced entry text: tag membership and count (rule 1), position of the effect statement (rule 2), absence of identifiers, ticket numbers, and file paths (rules 3–5), and entry count against the PR's set of independent user-visible changes (rules 6–7).
- **R4 Atomic obligations.** Rules 3, 4, and 5 are already split into one prohibition each. Rule 7 is a condition–action–exception clause sharing one trigger (a multi-change PR) and may stay as a single unit.
- **R5 Reachable precedence.** Rules 6 and 7 can conflict on a realistic input (a PR bundling several independent changes), and rule 7 states explicitly that it takes precedence. No other pair prescribes incompatible outcomes for the same decision.

Not flagged (false-positive guard): Context sentence 1 is rationale that degrades gracefully if lost and is correctly outside `## Rules`. Context sentence 2 is a load-bearing environmental fact, not a directive, and is correctly outside `## Rules`. Rule 7's trailing precedence clause restates its own condition, which is redundant prose but not a separation defect; general prose brevity is out of scope.

## Safety note

None. The target contains no instructions directed at the auditor and no attempt to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.
Safety notes: 0 (reported separately, excluded from counts).

This document cleanly separates context from constraints. Background rationale and the invocation fact live in `## Context`; all binding rules are numbered items in `## Rules`, each with explicit strength, each verifiable against the entry text, each stating a single obligation or a single condition–action–exception unit, and the one reachable conflict (rules 6 and 7) carries explicit precedence. No rewrites are required and no author decisions are outstanding.
