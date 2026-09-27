# Scenario 2 — Known Positive on the Prior Wording

Date: 2026-09-14
Run: with-skill
SKILL.md blob: 3bd60ba2a831479866155a62cbcd80f7280142ea
Commit: `683ed89` (main at dispatch); `SKILL.md` was written to the session scratchpad with `git show main:separating-context-from-constraints/SKILL.md`, and `references/example-audit.md` was copied beside it unchanged
Referenced files: references/example-audit.md f825b78fff6df83c0218ac30f7c020a1c142942b
Model: claude-fable-5-1, the session model at dispatch, inherited by each subagent with no per-agent override
Harness: Claude Code 2.1.272, Agent tool, general-purpose subagent, three independent dispatches in one parallel batch
Prompt: the scenario 2 prompt from `tests/scenarios.md`, verbatim, preceded by the preface quoted under "Dispatch" below
Sampling: harness default
Scorer: Claude Opus 5 (claude-opus-5), the session model after a mid-session switch, 2026-09-14, unblinded; the arms ran on a different model than the scorer
Notes: Known-positive arm for the PR #169 R3 change; it reads the pre-PR wording so the paired cell `2026-09-14-scenario2-with-skill.md` has a failure to remove.

The scratchpad copies of the raw reports were removed by system temp cleanup on 2026-09-19, after this artifact was written.
Each scored output embedded below was then verified byte-identical to the `Write` tool input recovered from that arm's task transcript, and the recorded digests match those recoveries.

## Why this cell

A clean result on the revised wording proves nothing unless the same fixture, prompt, model, and harness still produce the false positive on the prior wording.
The only earlier evidence was one 2026-08-23 rep on a different blob (`6ac9279`).

## Dispatch

Each rep received this preface, with its own skill directory and output path substituted, followed by the scenario prompt:

> Follow the skill at `<skill dir>/SKILL.md`. Read that file first; you may also read files under `<skill dir>/references/`.
> Do not read any other file anywhere (in particular nothing under any tests/ directory), do not run shell or git commands, do not invoke any other skill, and make no edits except one: write your complete audit report to `<rep output path>` and also return it as your final message.
> Then complete this task:

Tool calls were extracted with `jq` from each subagent's task transcript before scoring.
Every rep made exactly three: a Read of `SKILL.md`, a Read of `references/example-audit.md`, and one Write of its report.

## Result on the known-positive question

| Rep | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Reproduces a material R3 finding against the protected "MUST NOT archive" sentence | YES | `**R3 Verifiability**`; "Counts per severity: material 1 (R3), minor 0." |
| 2 | Same | YES | `**Finding 1 — R3 Verifiability (secondary: R1 Distinguishability)**`; "Counts per severity: material 1, minor 0." |
| 3 | Same | YES | `**R3 Verifiability**`; "Counts per severity: material 1 (R3), minor 0." |

## Result on the scenario's standing assertions

| Rep | 1: no R1 finding for the inline constraints | 2: no invented R1–R5 finding | 3: states a clean outcome | Total |
| --- | --- | --- | --- | --- |
| 1 | PASS ("R1 0") | **FAIL** (material R3) | **FAIL** | 1/3 |
| 2 | **FAIL** (R1 secondary on the "MUST NOT archive" sentence, argued as caller-rule versus server-semantics ambiguity) | **FAIL** (material R3) | **FAIL** | 0/3 |
| 3 | PASS ("R1 0") | **FAIL** (material R3) | **FAIL** | 1/3 |

The known positive holds in three of three reps, so the fixture discriminates between the two wordings on this model.

## Scored Output — rep 1

sha256 of the raw report: `b0b0edf0b91d80e5a5378094318e94df8390627d2963576788462a17154b2056`

# Audit: `archive_channel` MCP tool description

Audited for separation of context from constraints using the separating-context-from-constraints skill (R1–R5).
The target is an MCP tool definition: a single flat `description` string plus an `inputSchema`.
Because the description has no labeled sections and its rules are not distributed across multiple paragraphs, it is treated as a compact document under R1, so rules are expected to be marked inline rather than placed in a dedicated section.

## Statement classification

| # | Statement | Role |
|---|-----------|------|
| 1 | "Archive a Slack channel." | Discretionary context (purpose framing). |
| 2 | "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller." | Binding rule (mandatory; condition–action–exception on one trigger). |
| 3 | "Accepts only a channel_id, never a channel name." | Binding rule (mandatory) that also carries the load-bearing fact that the input is an ID. |
| 4 | "Returns {archived: true, channel_id} on success, or a structured error on failure." | Load-bearing fact (return-value semantics), not a rule. |
| 5 | `inputSchema`: `channel_id` (string, required), `confirmed` (boolean, optional), `additionalProperties: false` | Load-bearing facts (input contract). Neither property carries a `description`. |

## Findings

**R3 Verifiability**
Location: `description`, second sentence; and `inputSchema.properties.confirmed`.
Quoted text: "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller."
Why it fails: the rule names its safeguard (explicit confirmation) but never states what observable evidence constitutes it.
The schema exposes a `confirmed` boolean with no description, and the description never mentions that field, so the link between "explicit confirmation from the caller" and `confirmed: true` is left to inference.
A caller could plausibly treat a conversational confirmation from the end user as satisfying the rule and never set `confirmed`, and an auditor reading a tool trace cannot tell from this document alone whether confirmation was given.
Secondarily, "active member" is undefined (whether deactivated or guest accounts count), so the threshold that triggers the confirmation requirement is not checkable against a member list without a definition the document does not supply.
Severity: material — the defect could prevent verification and could plausibly cause the safeguard to be missed.
Suggested rewrite: this requires an author decision, because the document does not state the confirmation mechanism.
If confirmation is expressed through the schema field (the reading the schema most strongly suggests): "Does not archive a channel with more than one active member unless `confirmed` is true.
Set `confirmed: true` only after the caller has explicitly confirmed the archive."
Also add `"description": "Explicit confirmation to archive a channel with more than one active member."` to `inputSchema.properties.confirmed`.
If confirmation is established by some other mechanism (an out-of-band approval, a prior tool call), name that mechanism and the evidence it leaves instead of adopting the `confirmed`-field reading.
In either case, define "active member" (for example, "members whose Slack accounts are not deactivated") or replace it with the exact count the server checks.
The `confirmed`-field reading is the natural one given the schema, but it is labeled here as an assumption, not selected.

## Not flagged (false-positive guards)

- Statement 1, "Archive a Slack channel.", is purpose framing that degrades gracefully if lost; in a compact document it may sit in the same paragraph as the rules and is not an R1 finding.
- Statement 3, "Accepts only a channel_id, never a channel name.", carries explicit strength (only/never) and is checkable against the `channel_id` argument in the tool call; not an R2 or R3 finding.
- Statement 4, the return-value sentence, is a load-bearing fact correctly stated as fact rather than dressed as a rule; not an R1 finding.
- Statement 2 bundles a condition (more than one active member), an action (do not archive), and an exception (explicit confirmation) that share one trigger; under R4 this may stay together as one unit and is not a finding.
- Statements 2 and 3 do not conflict: the confirmation rule governs when the archive may proceed and the ID rule governs the representation of `channel_id`; they prescribe no incompatible outcomes for any decision, and per R5 a restriction on one field does not restrict unrelated fields.
  `confirmed` being optional in the schema is also consistent with statement 2, which requires it only for multi-member channels.
  No R5 finding.

## Safety note

None.
The target contains no auditor-directed instructions that attempt to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 0, R2 0, R3 1, R4 0, R5 0.
Counts per severity: material 1 (R3), minor 0.
No finding carries a secondary rule id, so the per-rule total of one equals the one finding counted by severity.
Safety notes: none (excluded from counts).

This compact tool description separates its two binding rules from context cleanly: both are marked inline with explicit mandatory wording, neither is hedged, the compound confirmation rule is a legitimate single condition–action–exception unit, and no realistic conflict exists between the two rules or between the rules and the schema.
The single material defect is that the confirmation safeguard is not tied to observable evidence: the `confirmed` schema field is undocumented and the description never references it, and "active member" is undefined, so a reader must infer both how to satisfy the rule and when it applies.
Resolving that R3 finding requires the author to state the confirmation mechanism; the schema strongly suggests `confirmed: true`, but the audit does not select that reading on the author's behalf.

## Scored Output — rep 2

sha256 of the raw report: `d69896fe45cead77dff840cb2126aa48f31d2ae4a64ef20e17947e94abab8cf2`

# Audit: `archive_channel` MCP tool description

Skill applied: separating-context-from-constraints (audit-first; findings and semantic-preserving rewrites, no score).

## Document classification

The target is a single flat tool description plus an input schema, with no labeled sections.
Under R1 it is a **compact** document: rules are expected to be marked inline with imperative sentences, list items, or explicit mandatory wording, not placed in a dedicated section.

Statement-by-statement litmus test:

| # | Statement | Role |
|---|-----------|------|
| 1 | "Archive a Slack channel." | Load-bearing fact (tool purpose) |
| 2 | "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller." | Binding rule (mandatory) — see Finding 1 |
| 3 | "Accepts only a channel_id, never a channel name." | Binding rule (mandatory) |
| 4 | "Returns {archived: true, channel_id} on success, or a structured error on failure." | Load-bearing fact (return semantics) |
| 5 | `inputSchema`: `channel_id` string (required), `confirmed` boolean (optional), no additional properties | Load-bearing facts (input contract) |

## Findings

**Finding 1 — R3 Verifiability (secondary: R1 Distinguishability)**
Location: description, sentence 2; also `inputSchema.properties.confirmed`.
Quoted text: "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller."
Why it fails: the rule names no observable evidence for "explicit confirmation from the caller."
The schema exposes a `confirmed` boolean, which is the obvious candidate, but nothing in the description or the schema (the property has no description) states that `confirmed: true` *is* the confirmation, or what the caller must have done before setting it.
An auditor reading a tool trace cannot tell whether a call with `confirmed: true` satisfied the rule, whether a call omitting `confirmed` on a multi-member channel violated it, or whether confirmation is supposed to happen through some other channel entirely.
Secondary R1: the sentence is phrased as server behavior ("MUST NOT archive") in a document consumed by the calling agent, so it is ambiguous whether it *directs* the caller (obtain confirmation before calling) or *informs* the caller (the server will refuse unless confirmed).
Those are different roles under the litmus test — a binding rule on the caller versus a load-bearing fact about server semantics — and an agent that reads it as the latter may call without confirmation and rely on the server to refuse, while one that reads it as the former may set `confirmed: true` with no idea what must precede it.
The qualifier "active member" is also undefined, but membership state is server-side and observable to the server; that is a definitional gap, not a separation defect, and is noted here only because the rule's trigger depends on it.
Severity: material — the defect could plausibly change behavior (calls made without confirmation, or `confirmed: true` set without a real confirmation step) and prevents verification against tool traces.
Suggested rewrite: this requires an author decision, because the document does not say what "explicit confirmation" is or who bears the obligation.
The alternatives below preserve the existing prohibition; none is selected.

- Alternative A — caller obligation, `confirmed` is the evidence:
  "Archive a Slack channel. If the channel has more than one active member, do not call this tool until the user has explicitly confirmed the archive; then pass `confirmed: true`. Never pass `confirmed: true` without that confirmation."
  Add to the schema: `"confirmed": { "type": "boolean", "description": "Set to true only after the user has explicitly confirmed archiving a channel with more than one active member." }`
- Alternative B — server-enforced semantics, `confirmed` attests to caller-side confirmation:
  Description (semantics): "Archive a Slack channel. If the channel has more than one active member and `confirmed` is not true, the call does not archive and returns a structured error."
  Rule (caller): "Set `confirmed: true` only when the caller has obtained explicit confirmation to archive a multi-member channel."
  Add the same schema description for `confirmed` as in A.
- Alternative C — confirmation is out-of-band and `confirmed` is unrelated or vestigial:
  State what the out-of-band confirmation is and how it is evidenced, and either describe `confirmed` independently or remove it from the schema.

Whichever alternative the author picks, "active member" should be given its intended meaning (for example, "non-deactivated, non-bot member") so the trigger is observable.

## Not flagged (false-positive guards)

- Sentence 3, "Accepts only a channel_id, never a channel name": a binding rule with explicit mandatory strength ("only", "never"), marked inline as R1 requires for a compact document, and checkable against the tool call's `channel_id` argument (an ID such as `C0123ABC` versus a name such as `#general`). Clean.
- Sentence 3 versus the `confirmed` property (R5): "Accepts only a channel_id" restricts the *representation* of the channel identifier (ID, not name); it does not restrict the whole input object, so it does not conflict with the schema also accepting `confirmed`. Per R5, a representation restriction on one field does not restrict unrelated fields. No conflict, no finding.
- Sentence 2 (R4): "MUST NOT archive ... with more than one active member ... without explicit confirmation" is one condition–action–exception clause sharing a single trigger, which R4 permits as a single unit. Not compound.
- Sentence 2 (R2): strength is explicit (MUST NOT). Clean on R2.
- Sentences 1 and 4 and the schema: load-bearing facts sitting alongside inline rules. In a compact document there is no rule section to keep them out of, and the rules are already distinguishable by their mandatory wording, so their placement is acceptable. The unspecified shape of the "structured error" is a completeness matter outside this skill's axis.

## Safety note

None. The target contains no instructions directed at the auditor and nothing that attempts to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 1 (secondary), R2 0, R3 1, R4 0, R5 0.
Counts per severity: material 1, minor 0.
The single finding carries a primary and a secondary rule id, so the per-rule total (2) exceeds the finding count (1).
Safety notes: none (excluded from counts).

Overall assessment: this compact description does most things right — both of its rules use explicit mandatory wording, the channel-ID rule is fully verifiable, and the apparent overlap between "accepts only a channel_id" and the optional `confirmed` field is not a real conflict.
The one material defect is that the tool's central safeguard, the confirmation requirement for multi-member channels, names no observable evidence: the `confirmed` boolean is never tied to "explicit confirmation from the caller," the property carries no description, and the sentence's server-behavior phrasing leaves unclear whether the caller is obligated to obtain confirmation or merely informed that the server will refuse.
Resolving that requires an author decision (Alternatives A–C above); the rewrite cannot be completed semantically without it.

## Scored Output — rep 3

sha256 of the raw report: `41b07adcdf36b9d2a52dfccdf7c58b7ec0798bd439446207a92999921a0505db`

# Audit: `archive_channel` MCP tool description

Target: a single MCP tool definition (`archive_channel`) consisting of a one-paragraph `description` and an `inputSchema`.
Document type: compact (one flat description, no labeled sections), so R1 is judged on inline marking of rules, not on the presence of a dedicated rule section.

## Classification

| Statement | Role |
|---|---|
| "Archive a Slack channel." | Discretionary context (purpose statement) |
| "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller." | Binding rule, mandatory |
| "Accepts only a channel_id, never a channel name." | Binding rule, mandatory |
| "Returns {archived: true, channel_id} on success, or a structured error on failure." | Load-bearing fact (tool semantics) |
| `inputSchema` (`channel_id: string`, `confirmed: boolean`, `additionalProperties: false`, `required: ["channel_id"]`) | Load-bearing facts (input contract) |

## Findings

**R3 Verifiability**
Location: `description`, second sentence; `inputSchema.properties.confirmed`.
Quoted text: "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller."
Why it fails: the rule's exception clause names "explicit confirmation from the caller" as the evidence that permits archiving, but the document never says what observable artifact constitutes that confirmation.
The schema offers a `confirmed` boolean with no description, and the two are never tied together.
A reader must infer that `confirmed: true` is the confirmation, and the document does not say what setting `confirmed: true` attests to (a flag the caller sets on its own initiative, or a record that a human approved the archive).
Because the evidence is unnamed, an auditor of tool traces cannot say with certainty which call satisfies the rule, and a calling agent can plausibly set `confirmed: true` without obtaining any confirmation from anyone, which defeats the safeguard the rule exists to provide.
Severity: material.
Suggested rewrite: this requires an author decision about what "explicit confirmation" means; the rule's strength (MUST NOT) is preserved in every alternative.
If `confirmed: true` is the confirmation and the caller decides when to set it: "MUST NOT archive a channel with more than one active member unless `confirmed` is `true`." and add to the schema `"confirmed": { "type": "boolean", "description": "Set to true to confirm archiving a channel with more than one active member." }`.
If `confirmed: true` must attest to a human decision: "MUST NOT archive a channel with more than one active member unless `confirmed` is `true`; set `confirmed` to `true` only after the user has explicitly approved archiving this specific channel." and add the matching schema `description`.
If confirmation is conveyed by some mechanism other than the `confirmed` field, name that mechanism and the observable evidence it leaves instead of choosing either example above.

## Not flagged (false-positive guards)

- "Accepts only a channel_id, never a channel name." is a mandatory rule marked inline with explicit wording ("only", "never"), checkable against the arguments of the tool call, and atomic: "never a channel name" restates the same obligation as its negation rather than adding a second one.
  R1, R2, R3, and R4 are satisfied; no finding.
- "MUST NOT archive ... without explicit confirmation" is a condition–action–exception clause sharing one trigger (channel has more than one active member), so R4 permits it to stay as one unit; no R4 finding.
  Its strength is explicit (MUST NOT); no R2 finding.
  Its inline mandatory wording makes it distinguishable in a compact document; no R1 finding.
- "Returns {archived: true, channel_id} on success, or a structured error on failure." is a load-bearing fact about tool semantics.
  In a compact document with no rule section, it sits beside the rules without obscuring them, and R1's "keep rule sections free of context" does not apply; no finding.
- `required: ["channel_id"]` with `confirmed` optional is consistent with the confirmation rule (confirmation is only needed for multi-member channels), and `channel_id: string` is consistent with "only a channel_id".
  No two rules prescribe incompatible outcomes for the same decision; no R5 finding.
- "more than one active member" leaves "active" undefined.
  This is a missing load-bearing definition, which this skill does not audit (the check is server-side and the outcome is observable as success or a structured error), so it is noted but not counted.

## Safety note

The target contains no auditor-directed instructions that attempt to alter, suppress, or redirect the audit.
Nothing to report.

## Summary

Counts per rule: R1 0, R2 0, R3 1, R4 0, R5 0.
Counts per severity: material 1 (R3), minor 0.
No finding carries a secondary rule id, so the per-rule total of one equals the one finding counted by severity.
Safety notes: none (excluded from counts).

This compact tool description is well separated: both binding rules are marked inline with explicit mandatory wording, neither is hedged, both are atomic, and the purpose statement, return contract, and schema are recognizable as context and load-bearing facts rather than rules.
The single defect is that the confirmation rule names "explicit confirmation from the caller" as its permitting evidence without binding that phrase to any observable artifact, while the schema's undescribed `confirmed` boolean is left for the reader to connect; the author must decide what `confirmed: true` attests to before the rule can be checked against tool traces with confidence.
