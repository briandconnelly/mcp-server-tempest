# Scenario 8 — With-Skill Confirmation Cell

Date: 2026-08-23
Run: with-skill
SKILL.md blob: 634c54baf6f25bec7641c638c9a5923c7f58bc92
Commit: none — run against the uncommitted working tree on branch `consolidate-context-skill`
Referenced files: references/example-audit.md f37434323829b1da823ed4dfe0b6e12b8fc19dad
Model: claude-fable-5, the session model, inherited by the subagent with no per-agent override
Harness: Claude Code 2.1.241, Agent tool, general-purpose subagent, single dispatch
Sampling: harness default
Scorer: Claude (session model), 2026-08-23, unblinded
Prompt: the scenario 8 prompt from `tests/scenarios.md`, verbatim, preceded by instructions to follow `SKILL.md`, to read no file under `tests/`, and to make no edits
Notes: later commits on this branch edited `SKILL.md` after this arm read it (a rationale sentence and pointer-only wording; no decision point traverses them); the results table in `tests/scenarios.md` lists the cells each edit owed. Confirmation cell for the R5 author-decision pointer.

## Why this cell

Four `SKILL.md` edits landed in one batch: the three R3 examples moved from the Rules section to Core Concept; R1's "one finding per misplaced statement, even when both directions of the defect are present" folded into Finding Format's consolidation rule; R3's and R5's author-decision sentences reduced to pointers at Finding Format; and the Core Concept rationale's untested long-context claim softened to the structural claim.
This cell is owed under the [measurement protocol](../scenarios.md#measurement-protocol) adopted in `tests/scenarios.md`: paraphrases were removed while their authoritative statements stayed, and the edited sentences sit on this cell's decision point.
Scenario 8 is the R5 cell: a reachable conflict with no stated precedence, so the audit must reach the author-decision contract through R5's new pointer and still present every plausible precedence choice.

## Result on the edited decision point

| # | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | R5 reaches the author-decision contract via the pointer and presents every plausible precedence choice | PASS | "this requires an author decision between two plausible precedence policies"; EU-wins and global-wins both given. |
| 2 | Natural reading labeled as assumption, not selected | PASS | "The EU-wins reading is the natural specific-over-general interpretation, but it is labeled here as an assumption, not selected by the audit." |

## Result on the scenario's standing assertions

| # | Assertion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | One material R5 finding for the pair | PASS | "Counts per rule: … R5 1"; "material 1 (R5)". |
| 2 | Attaches to and quotes both statements | PASS | Location "lines 5-6"; both sentences quoted. |
| 3 | Both precedence policies presented as author decisions | PASS | See edited-decision-point row 1. |
| 4 | Does not silently select the specific-over-general reading | PASS | See edited-decision-point row 2. |

## Scored Output

I have everything needed; the audit follows.

# Audit: `upload-router`

## Findings

**R5 Reachable precedence**
Location: lines 5-6 (`## Rules`, items 1 and 2).
Quoted text: "Always use the global endpoint for uploads." / "For EU customer uploads, use the EU endpoint."
Why it fails: the two rules prescribe incompatible outcomes for the same decision on a realistic input — an upload from an EU customer. Rule 1 is unconditional ("Always") and names the global endpoint; rule 2 names the EU endpoint for a subset of the same uploads. The document does not state which rule wins, so an agent handling an EU customer upload cannot determine the correct endpoint from the document alone.
Severity: material.
Suggested rewrite: this requires an author decision between two plausible precedence policies.
If the specific EU rule wins: "Use the global endpoint for uploads by default; for EU customer uploads, use the EU endpoint, which takes precedence over the global default."
If the global rule wins: "Always use the global endpoint for uploads, including EU customer uploads; do not use the EU endpoint."
The EU-wins reading is the natural specific-over-general interpretation, but it is labeled here as an assumption, not selected by the audit.

Not flagged (false-positive guard): both statements are correctly placed in a labeled `## Rules` section, use imperative wording (R1), carry unambiguous mandatory strength — "Always" and an unhedged imperative (R2), are checkable against the endpoint used in tool calls (R3), and each states one obligation (R4). The document contains no context or load-bearing facts inside the rule section and no rules outside it.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 1.
Counts per severity: material 1 (R5), minor 0.
No finding carries a secondary rule id, so the per-rule total of one equals the one finding counted by severity.
Safety note: none — the document contains no auditor-directed instructions.

The document is structurally clean: both statements are binding rules, placed in a dedicated rules section, with explicit strength, verifiable outcomes, and atomic obligations. Its single defect is a reachable conflict between an unconditional global-endpoint rule and a conditional EU-endpoint rule with no stated precedence, which could plausibly change behavior on every EU customer upload. That finding requires an author decision before a rewrite can claim to preserve intended behavior.
