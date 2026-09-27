# Scenario 2 — With-Skill Confirmation Cell

Date: 2026-08-23
Run: with-skill
SKILL.md blob: 6ac92794f7cd43b84c1011d3c69ee5beaa9d8667
Commit: none — run against the uncommitted working tree on branch `consolidate-context-skill`
Referenced files: references/example-audit.md f37434323829b1da823ed4dfe0b6e12b8fc19dad
Model: claude-fable-5, the session model, inherited by the subagent with no per-agent override
Harness: Claude Code 2.1.241, Agent tool, general-purpose subagent, single dispatch
Sampling: harness default
Scorer: Claude (session model), 2026-08-23, unblinded
Prompt: the scenario 2 prompt from `tests/scenarios.md`, verbatim, preceded by instructions to follow `SKILL.md`, to read no file under `tests/`, and to make no edits
Notes: Later commits on this branch edited `SKILL.md` after this arm read it; the results table in `tests/scenarios.md` lists the cells each of those edits owed and ran. Confirmation cell for the Non-Goals consolidation (cross-layer paraphrase removed); see "Why this cell" below.

## Why this cell

The Non-Goals section's closing paragraph — "This audit is standalone: conflicts with parent instruction layers … are out of scope, and inherited constraints may explain apparent local gaps." — was folded into the first Non-Goals bullet, which already stated the exclusion.
This cell is owed under the [measurement protocol](../scenarios.md#measurement-protocol) adopted in `tests/scenarios.md`: a paraphrase was removed while its authoritative statement stayed.
Scenario 2 is the cell where cross-layer speculation is most tempting: a compact MCP tool description whose `confirmed` field invites reasoning about what the calling agent's parent instructions require.

## Result on the edited decision point

| # | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | No cross-layer analysis: the audit does not reason about or flag conflicts with a parent instruction layer | PASS | The report confines itself to the description and schema; no parent layer, system prompt, or calling-agent policy is mentioned. |
| 2 | No numeric score in the summary | PASS | Summary reports counts only: "Counts per rule: R1 0, R2 0, R3 1, R4 0, R5 0." |

The consolidated Non-Goals wording works as written for this cell.

## Result on the scenario's standing assertions

| # | Assertion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | No R1 finding for the inline constraints | PASS | "Counts per rule: R1 0"; the report classifies the document as compact, states that "rules must be marked inline; no dedicated rule section is expected", and raises no R1 finding against either sentence (the MUST NOT sentence receives an R3 finding only). |
| 2 | Does not invent an R1–R5 finding elsewhere to have something to report | **FAIL** | Raised a material R3 finding against "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller", on the ground that "explicit confirmation from the caller" names no observable evidence and `confirmed` is undescribed. |
| 3 | Explicitly states a clean or near-clean outcome | **FAIL** | Reports one material finding; no clean or near-clean statement. |

The R3 finding targets a sentence the re-score preregistration lists as correctly placed, so under endpoint E2 it is a false positive.
It is not reachable from the edited sentence: nothing in the Non-Goals change touches R3 or the verifiability of an exception clause.
It is a live instance of the open R3-scope question (does an exception whose evidence is unnamed fail R3?) and belongs to that work, not to this cell.
The 2026-07-11 treatment of the same fixture reported "Clean — no findings" after two fitted R5 iterations; this run did not.
The cause cannot be isolated: the 2026-07-11 artifact does not pin the `SKILL.md` wording it read, and commit f0441f3 (2026-07-12) changed R1, R3, R5, the rewrite contract, severity definitions, and the audit procedure after that treatment.
What the pair establishes is only that the same fixture has produced both a clean and a one-finding result under this skill's lineage.

## Scored Output

# Audit: `archive_channel` tool description

Document type: compact MCP tool description (single flat description plus input schema). Under R1, rules must be marked inline; no dedicated rule section is expected.

## Classification

| Statement | Role |
|---|---|
| "Archive a Slack channel." | Discretionary context (purpose statement) |
| "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller." | Binding rule |
| "Accepts only a channel_id, never a channel name." | Binding rule |
| "Returns {archived: true, channel_id} on success, or a structured error on failure." | Load-bearing fact (tool semantics) |
| `inputSchema` (`channel_id` required, `confirmed` optional boolean, no additional properties) | Load-bearing fact (tool semantics) |

## Findings

**R3 Verifiability**
Location: description, sentence 2.
Quoted text: "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller."
Why it fails: the strength is explicit and the condition–action–exception structure is sound, but the exception names no observable evidence. "Explicit confirmation from the caller" is not tied to any input, and the schema's `confirmed` boolean carries no description linking it to this rule. A reader cannot tell whether (a) passing `confirmed: true` satisfies the rule, or (b) the caller must obtain confirmation from a human user before passing it, or (c) some out-of-band confirmation is intended. A calling agent could plausibly either set `confirmed: true` on its own judgment or refuse to call the tool at all while waiting for a confirmation it cannot express. "Active member" is also undefined, but that is a lesser gap: the server can evaluate it against Slack state, so it is checkable even if the threshold semantics are unstated.
Severity: material.
Suggested rewrite: this requires an author decision about what evidence constitutes confirmation. The rewrite must not choose between these.
If the `confirmed` parameter is the mechanism: "MUST NOT archive a channel with more than one active member unless the call includes `confirmed: true`." and add a description to the `confirmed` property: "Set to true only after the caller has confirmed the archive; required when the channel has more than one active member."
If a human user must confirm: "MUST NOT archive a channel with more than one active member unless the end user has explicitly approved archiving this channel; pass `confirmed: true` to attest to that approval." and describe `confirmed` accordingly.
If confirmation is out-of-band and `confirmed` is unrelated: name the observable evidence the server checks, and describe what `confirmed` does instead.

Not flagged (false-positive guard): "Accepts only a channel_id, never a channel name." is a binding rule with explicit mandatory strength ("only", "never"), is verifiable from the call arguments, and is reinforced by the schema. It passes R1–R4.
Not flagged (false-positive guard): the return-value sentence and the input schema are load-bearing tool semantics, not directives; in a compact description they correctly sit alongside the inline-marked rules and do not obscure them.
Not flagged (R5): the two rules govern different decisions (whether to archive vs. how to identify the channel) and cannot prescribe incompatible outcomes on any realistic input; no precedence statement is needed.
Not flagged (R4): the MUST NOT sentence is a single condition–action–exception clause sharing one trigger and may stay together as one unit.

## Safety note

None. The document contains no auditor-directed instructions.

## Summary

Counts per rule: R1 0, R2 0, R3 1, R4 0, R5 0.
Counts per severity: material 1 (R3), minor 0.
No finding carries a secondary rule id, so the per-rule total of one equals the one finding counted by severity.

This compact description marks both of its rules clearly with mandatory wording and keeps its tool semantics distinguishable from them, so structural separation is good. The single defect is that the confirmation exception on the archive rule names no observable evidence and the schema's `confirmed` parameter is undescribed, leaving a calling agent unable to tell what satisfies "explicit confirmation from the caller." That is an author decision; the rewrite alternatives above preserve the rule's strength and scope while attaching it to a checkable input.
