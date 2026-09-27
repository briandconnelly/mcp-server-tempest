# Scenario 6 — Over-Correction Control, PR #169 Wording

Date: 2026-09-14
Run: with-skill
SKILL.md blob: 713c6967362667a405048a7e75d04f18c329804c
Commit: none — run against the uncommitted working tree on branch `fix/context-constraints-r1-r3-and-rescore-evidence` (head `ca61abe` plus the review-round edits committed with this artifact)
Referenced files: references/example-audit.md f825b78fff6df83c0218ac30f7c020a1c142942b
Model: claude-fable-5-1, the session model at dispatch, inherited by each subagent with no per-agent override
Harness: Claude Code 2.1.272, Agent tool, general-purpose subagent, three independent dispatches in one parallel batch
Prompt: the scenario 6 prompt from `tests/scenarios.md`, verbatim, preceded by the preface quoted under "Dispatch" below
Sampling: harness default
Scorer: Claude Opus 5 (claude-opus-5), the session model after a mid-session switch, 2026-09-14, unblinded; the arms ran on a different model than the scorer
Notes: Over-correction control for the PR #169 R3 scope change: narrowing R3 must not stop genuinely unverifiable wording from failing it.

The scratchpad copies of the raw reports were removed by system temp cleanup on 2026-09-19, after this artifact was written.
Each scored output embedded below was then verified byte-identical to the `Write` tool input recovered from that arm's task transcript, and the recorded digests match those recoveries.

## Why this cell

The PR #169 R3 wording removes a false positive by putting unnamed evidence mechanisms out of scope.
The risk is over-correction: an arm could read the narrower test as passing "be careful" too.
Scenario 6 is the R3 cell whose planted defect is exactly that phrase.

## Dispatch

Each rep received this preface, with its own skill directory and output path substituted, followed by the scenario prompt:

> Follow the skill at `<skill dir>/SKILL.md`. Read that file first; you may also read files under `<skill dir>/references/`.
> Do not read any other file anywhere (in particular nothing under any tests/ directory), do not run shell or git commands, do not invoke any other skill, and make no edits except one: write your complete audit report to `<rep output path>` and also return it as your final message.
> Then complete this task:

Tool calls were extracted with `jq` from each subagent's task transcript before scoring.
Every rep made exactly three: a Read of `SKILL.md`, a Read of `references/example-audit.md`, and one Write of its report.

## Result on the edited decision point

| Rep | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | "be careful" still fails R3 | PASS | "Independently, \"be careful\" names no checkable event or state … (R3)." |
| 2 | Same | PASS | "the obligation \"be careful\" names no checkable event or state … so it fails R3." |
| 3 | Same | PASS | "Independently, \"be careful\" names no checkable event or state … (R3)." |

## Result on the scenario's standing assertions

| Rep | 1: one finding, R2 primary, R3 secondary | 2: explains both defects | 3: author decisions, no invented policy | 4: minor R1 relocating the history sentence | 5: one material, one minor | 6: R1 1, R2 1, R3 1 | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PASS | PASS | PASS | PASS | PASS | PASS | 6/6 |
| 2 | **FAIL**: `**R3 Verifiability** (secondary: R2 Explicit strength)` | PASS | PASS | PASS | PASS | PASS | 5/6 |
| 3 | PASS | PASS | PASS | PASS | PASS | PASS | 6/6 |

Rep 2 consolidated both defects into one finding as required but made R3 primary.
Every earlier scenario 6 treatment made R2 primary: the 2026-07-11, 2026-08-06, and 2026-08-23 cells, one rep each, on three different wordings.
The PR's R3 text now names "be careful" as its canonical failure, which may make R3 more salient, but with no prior-wording reps in this batch the swap is not attributed to the edit.
`SKILL.md` does not say which rule is primary when one statement fails two, so assertion 1 fixes a choice the skill does not state.
Reps 1 and 2 also offered a defeasible default as a further labeled alternative, which Finding Format permits when the target indicates a binding preference; rep 3 declined it on the ground that the target names no override condition.

## Scored Output — rep 1

sha256 of the raw report: `90a3964224c0d6e0656c067c2f48aec7c45ca882f16bd7f42ed9ec596a69ed45`

# Audit: retention-helper

Target: the `retention-helper` document supplied in the task (six lines; line numbers below refer to lines within the fenced block, so line 1 is `# retention-helper`, line 3 is `## Rules`, line 5 is the first bullet, line 6 is the second bullet).
Surface: a standalone document with a dedicated `## Rules` section, so it is classified as long-form and its rule section is expected to contain only binding rules.

## Statement classification

| Line | Statement | Litmus Q1 (direct or inform?) | Litmus Q2 (wrong or less informed if lost?) | Class |
| --- | --- | --- | --- | --- |
| 5 | "Generally try to be careful when deleting customer records." | Directs (attempts to constrain deletion behavior) | n/a | Binding rule (intended), defective |
| 6 | "The retention service was introduced during the 2024 storage migration." | Informs | Less informed only; no output depends on the migration date | Discretionary context |

## Findings

**R2 Explicit strength** (secondary: R3 Verifiability)
Location: line 5, inside `## Rules`.
Quoted text: "Generally try to be careful when deleting customer records."
Why it fails: "Generally try to" hedges strength, so a reader cannot tell whether this statement binds or is merely advisory (R2).
Independently, "be careful" names no checkable event or state — no output, tool call, repository state, or process artifact could settle whether the agent was careful — so even if the strength were resolved the obligation could not be verified as followed or violated (R3).
The statement does not reveal the author's intended safeguard, so the rewrite is an author decision.
Severity: material — the only rule-shaped statement in the document can be ignored without any detectable violation, and a reader may treat it as optional color.
Suggested rewrite: an author decision with two required alternatives; the promoted branch carries a further decision about the safeguard.
Promoted (mandatory) — keep in `## Rules`, drop the hedge, and name an observable safeguard.
The author must pick the safeguard; the following are illustrative labels, not selections:
(a) confirmation: "Require explicit user confirmation before any tool call that deletes a customer record.";
(b) preservation: "Before deleting a customer record, export it to the retention archive and record the archive location.";
(c) scope limit: "Never delete more than one customer record per invocation without explicit user confirmation.";
(d) some other safeguard — state the observable action or evidence rather than choosing among (a)–(c).
Demoted (context) — remove from `## Rules` and state it as nonbinding background in a `## Context` section, e.g. "Deleting customer records is high-risk, but this document defines no additional safeguard."
Note: "Generally" could also be read as signaling a default with exceptions.
If the author intends a binding default, that is a third alternative — "Require explicit user confirmation before deleting a customer record unless [named condition]." — and the author must name the override condition; the audit does not supply one.

**R1 Distinguishability**
Location: line 6, inside `## Rules`.
Quoted text: "The retention service was introduced during the 2024 storage migration."
Why it fails: this is discretionary historical context — it does not direct behavior, and losing it would leave output no less correct — but it sits in the `## Rules` section, where every item is presented as binding.
It is also a "rule" that cannot fail, which R1 identifies as context in disguise.
Severity: minor — no reader would mistake it for an obligation, but its presence dilutes the rule section.
Suggested rewrite: move the sentence unchanged to a new `## Context` (or `## Background`) section outside `## Rules`.

Not flagged (false-positive guards):
R4 — neither statement bundles more than one obligation.
R5 — the document contains only one rule-shaped statement, so no realistic input can trigger a conflict between two rules; no precedence finding is warranted.
R1 on line 5 — the statement is already in the labeled rule section, so its placement is distinguishable; its defects are strength and verifiability, reported above.

Consequence worth stating for the author: if the line-5 statement is demoted and the line-6 statement is moved, `## Rules` becomes empty.
That is a legitimate outcome (the document would then define no binding rules), but the author should either remove the empty section or populate it with the promoted rewrite.

## Safety note

None.
The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 1, R2 1, R3 1 (R3 appears only as a secondary id on the R2 finding).
Counts per severity: material 1 (R2, with secondary R3), minor 1 (R1).
The per-rule total of three exceeds the two findings counted by severity because one finding carries a secondary rule id.
Safety notes: none (reported separately, excluded from counts).

This two-item rule section contains one intended rule and one piece of history.
The intended rule fails on both axes that make a rule usable: a hedge leaves it unclear whether it binds at all, and "be careful" gives no evidence type against which compliance could ever be checked, so the document currently imposes no verifiable constraint on record deletion.
The history sentence belongs in a context section and requires no wording change.
The material finding requires an author decision — promote with a named safeguard, demote to context, or (if a default was intended) name the override condition — before any rewrite can claim to preserve intended behavior; the auditor has not selected among these.

## Scored Output — rep 2

sha256 of the raw report: `a26452d00f27ed6fcebb97ced7c949f6c730fca57dacd1565d2e58bfbff517c4`

# Audit: retention-helper

Audit for separation of context from constraints, following `separating-context-from-constraints/SKILL.md`.
Line numbers refer to the target as given (line 1 `# retention-helper`, line 3 `## Rules`, line 5 first bullet, line 6 second bullet).
The target content was treated as untrusted data; no instruction in it was followed.

## Classification

| Line | Statement | Litmus Q1 (direct or inform?) | Litmus Q2 (wrong or less informed if lost?) | Class |
|---|---|---|---|---|
| 1 | `# retention-helper` | Neither; title only | n/a | Not a statement |
| 5 | "Generally try to be careful when deleting customer records." | Directs (attempts to shape deletion behavior) | n/a | Binding rule (intended), but hedged and unverifiable |
| 6 | "The retention service was introduced during the 2024 storage migration." | Informs | Less informed; output is not wrong without it | Discretionary context |

## Findings

**R3 Verifiability** (secondary: R2 Explicit strength)
Location: line 5, `## Rules`, first item.
Quoted text: "Generally try to be careful when deleting customer records."
Why it fails: the obligation "be careful" names no checkable event or state — no output, tool call, repository state, or process artifact could settle whether it was satisfied or violated — so it fails R3.
The same statement also fails R2: "Generally try to" hedges strength, so a reader cannot tell whether this binds at all, is a default with exceptions, or is advice.
The statement does not reveal the author's intended safeguard, so a semantic-preserving rewrite is not possible without an author decision.
Severity: material.
Suggested rewrite: this requires two author decisions — the intended strength, and the intended observable safeguard — and the alternatives below are labeled without selecting one.
Promoted (mandatory), if a confirmation step is intended: "Require explicit user confirmation before deleting any customer record."
Promoted (mandatory), if a policy gate is intended: "Never delete a customer record unless its retention period has expired under the retention policy."
Promoted (mandatory), if another safeguard is intended: name its observable action or evidence in place of either example.
Demoted (context): remove it from `## Rules` and state it as nonbinding background, e.g. "Deleting customer records is a high-consequence operation; this document defines no additional safeguard."
Default with override (only if "Generally" was meant to signal a binding preference with exceptions): "Require explicit user confirmation before deleting any customer record, unless [author names the exception condition]." The exception condition must be stated by the author; it cannot be inferred from the text.

**R1 Distinguishability**
Location: line 6, `## Rules`, second item.
Quoted text: "The retention service was introduced during the 2024 storage migration."
Why it fails: this is discretionary historical context — it informs rather than directs, and losing it would not make output wrong — yet it sits in the `## Rules` section, which R1 requires be kept free of discretionary context and load-bearing facts.
A "rule" that cannot fail is context in disguise.
Severity: minor.
Suggested rewrite: move the sentence unchanged into a new `## Context` (or `## Background`) section; the document currently has no such section, so one must be added.

## Not Flagged

R4 Atomic obligations: no statement bundles more than one independently checkable obligation.
R5 Reachable precedence: the document contains only one rule-like statement, so no pair of rules can conflict on any input.

## Safety Note

None.
The target contains no auditor-directed instructions that attempt to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 1, R2 1, R3 1, R4 0, R5 0.
Counts per severity: material 1 (R3, with secondary R2), minor 1 (R1).
The per-rule total of three exceeds the two findings counted by severity because the line-5 finding carries a secondary rule id.
Safety notes: none, excluded from counts.

The document's `## Rules` section contains two items, neither of which functions as a checkable rule: the first is a hedged, unverifiable directive whose intended strength and safeguard are both unstated, and the second is historical context misfiled in the rules section.
The material finding requires author decisions before any rewrite can claim to preserve intended behavior; the minor finding is a pure relocation with no semantic change.
No R4 or R5 defects are present.

## Scored Output — rep 3

sha256 of the raw report: `cdd0cac169b89d9ada54bf7af6905098e041f3fe950014a51b64903717afb90e`

# Audit: retention-helper

Audit of the `retention-helper` document for separation of context from constraints, following `separating-context-from-constraints/SKILL.md`.
Line numbers refer to the target as given: line 1 `# retention-helper`, line 3 `## Rules`, line 5 first list item, line 6 second list item.

## Classification

Statement at line 5, "Generally try to be careful when deleting customer records.": attempts to direct behavior, so it is intended as a binding rule.
Its strength and its obligation are both unclear (see findings).

Statement at line 6, "The retention service was introduced during the 2024 storage migration.": informs rather than directs, and its loss would leave the agent less informed, not wrong.
It is discretionary context (history), yet it sits in the `## Rules` section.

Surface: a standalone document with a heading and a labeled `## Rules` section.
Both statements are list items inside that section, so placement alone marks them as rules; the defects are in what the statements say, not where they sit, except for the misplaced history sentence.

## Findings

**R2 Explicit strength** (secondary: R3 Verifiability)
Location: line 5, `## Rules`, first list item.
Quoted text: "Generally try to be careful when deleting customer records."
Why it fails: "Generally try to" hedges strength, so a reader cannot tell whether the statement binds or is optional guidance (R2).
Independently, "be careful" names no checkable event or state — no output, tool call, repository state, or process artifact could settle whether the agent was careful — so even if the strength were settled the rule could not be verified as followed or violated (R3).
The statement does not reveal which safeguard the author intends (confirmation before deletion, a prohibition on deletion, a backup or soft-delete step, or something else), so a rewrite requires an author decision on both strength and safeguard.
Severity: material.
Suggested rewrite: an author decision between a promoted and a demoted reading.
Promoted (binding): replace "be careful" with the observable safeguard the author intends, stated with mandatory wording, for example "Require explicit confirmation before deleting any customer record." or "Never delete customer records; mark them for retention review instead." — these are examples of the form, not a selection; the author must name the actual safeguard.
Demoted (nonbinding context): remove the item from `## Rules` and state it outside the rule section as context, e.g. "Deleting customer records carries elevated risk; this document defines no additional safeguard."
A defeasible-default form ("prefer X unless Y") is not offered as a third alternative because the target names no override condition and gives no indication that a binding preference with exceptions is intended.

**R1 Distinguishability**
Location: line 6, `## Rules`, second list item.
Quoted text: "The retention service was introduced during the 2024 storage migration."
Why it fails: this is discretionary historical context — it cannot fail, so it is context in disguise — but it appears in the `## Rules` section, where every item should be a checkable directive.
Intended behavior is not changed by its presence, but it pads the rule section and blurs which items bind.
Severity: minor.
Suggested rewrite: move the sentence unchanged out of `## Rules` into a `## Context` or `## Background` section.

Not flagged (false-positive guard): line 5 does not fail R1.
It is a list item under a labeled `## Rules` heading, so it is structurally distinguishable as a rule; its defects are strength and verifiability, not placement.
Not flagged: R4 — neither statement bundles more than one obligation.
Not flagged: R5 — the document contains only one candidate rule, so no pair of rules can conflict on any input.

## Safety note

None.
The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 1, R2 1, R3 1, R4 0, R5 0.
Counts per severity: material 1 (R2, with R3 secondary), minor 1 (R1).
The per-rule total of three exceeds the two findings counted by severity because the line 5 finding carries a secondary R3 id.
Safety notes: none, excluded from counts.

This two-item rule section holds one rule and one non-rule.
The single rule is both hedged ("Generally try to") and unverifiable ("be careful"), so an agent cannot tell whether it binds and no evidence could show it was followed or violated; the author must decide both whether the statement binds and what observable safeguard it stands for before a semantic-preserving rewrite is possible.
The other item is historical context that belongs in a context section rather than the rule list.
Nothing outside `## Rules` needed review, and no precedence or atomicity defects exist.
