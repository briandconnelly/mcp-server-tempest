# Scenario 2 — With-Skill Confirmation Cell, PR #169 Wording

Date: 2026-09-14
Run: with-skill
SKILL.md blob: 713c6967362667a405048a7e75d04f18c329804c
Commit: none — run against the uncommitted working tree on branch `fix/context-constraints-r1-r3-and-rescore-evidence` (head `ca61abe` plus the review-round edits committed with this artifact)
Referenced files: references/example-audit.md f825b78fff6df83c0218ac30f7c020a1c142942b
Model: claude-fable-5-1, the session model at dispatch, inherited by each subagent with no per-agent override
Harness: Claude Code 2.1.272, Agent tool, general-purpose subagent, three independent dispatches in one parallel batch
Prompt: the scenario 2 prompt from `tests/scenarios.md`, verbatim, preceded by the preface quoted under "Dispatch" below
Sampling: harness default
Scorer: Claude Opus 5 (claude-opus-5), the session model after a mid-session switch, 2026-09-14, unblinded; the arms ran on a different model than the scorer
Notes: Confirmation cell for the PR #169 R3 scope change, run in the same batch as its known positive on the prior wording (`2026-09-14-scenario2-with-skill-prior-wording.md`).

The scratchpad copies of the raw reports were removed by system temp cleanup on 2026-09-19, after this artifact was written.
Each scored output embedded below was then verified byte-identical to the `Write` tool input recovered from that arm's task transcript, and the recorded digests match those recoveries.

## Why this cell

PR #169 rewrote R3 to judge a rule's obligation rather than every term inside it, and to put naming the evidence mechanism out of scope.
The 2026-08-23 scenario 2 cell raised a material R3 finding against the protected "MUST NOT archive" sentence because its exception names no evidence mechanism (issue #159).
This cell is owed under the [measurement protocol](../scenarios.md#measurement-protocol): the edited R3 sentences sit on scenario 2's decision point.
Three reps were run on this wording and three on the prior wording, so the comparison has a known positive.
The two wordings differ by the whole PR #169 diff, not by the R3 sentences alone.

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
| 1 | The unnamed confirmation mechanism is not raised as an R3 finding | PASS | `**R3 Verifiability** — pass.`; "per R3, requiring the document to name the evidence mechanism is out of scope for this audit and is not a separation defect." |
| 2 | Same | PASS | "per R3 naming the evidence mechanism is out of scope and is not a separation defect. Passes." |
| 3 | Same | PASS | "R3 does not require the document to name the evidence mechanism, so the absence of a sentence tying \"explicit confirmation\" to the `confirmed` parameter is not a defect under this audit" |

## Result on the scenario's standing assertions

| Rep | 1: no R1 finding for the inline constraints | 2: no invented R1–R5 finding | 3: states a clean outcome | Total |
| --- | --- | --- | --- | --- |
| 1 | PASS ("Counts per rule: R1 0") | PASS ("material 0, minor 0") | PASS ("Clean — no findings.") | 3/3 |
| 2 | PASS ("Counts per rule: R1 0") | PASS ("material 0, minor 0") | PASS ("Clean — no findings.") | 3/3 |
| 3 | PASS ("Counts per rule: R1 0") | PASS ("material 0, minor 0") | PASS ("Clean — no findings.") | 3/3 |

All three reps still mention the undescribed `confirmed` field, as an unscored out-of-scope note carrying no rule id or severity.

## Scored Output — rep 1

sha256 of the raw report: `edd3217123115ce031ee2976ead3dfd42654806d1d9d1958b0e05b9946d5e481`

# Audit: `archive_channel` MCP tool description

Skill applied: separating-context-from-constraints (R1–R5, two-level severity).
Target: one MCP tool definition (`description` string plus `inputSchema`).

## Surface classification

Per R1, the target is classified by the surface that carries its instructions.
The `description` field is a single inline field, so it is a compact surface: rules are expected to be marked inline with imperative sentences, list items, or explicit mandatory wording, not placed in a dedicated section.
The `inputSchema` is a second, machine-readable surface that carries load-bearing facts (parameter names, types, which are required), not prose rules.

## Statement classification (two-question litmus test)

| # | Location | Statement | Role |
|---|----------|-----------|------|
| 1 | description, sentence 1 | "Archive a Slack channel." | Load-bearing fact (tool semantics: what the tool does) |
| 2 | description, sentence 2 | "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller." | Binding rule (condition–action–exception) |
| 3 | description, sentence 3 | "Accepts only a channel_id, never a channel name." | Binding rule (input representation restriction) |
| 4 | description, sentence 4 | "Returns {archived: true, channel_id} on success, or a structured error on failure." | Load-bearing fact (return contract) |
| 5 | inputSchema | `channel_id: string` (required), `confirmed: boolean` (optional), `additionalProperties: false` | Load-bearing facts (parameter contract) |

## Findings

Clean — no findings.

Each rule was run over the classified statements; the checks and their outcomes follow so the negative result is traceable.

**R1 Distinguishability** — pass.
Both binding rules (statements 2 and 3) are marked with explicit mandatory wording ("MUST NOT"; "only ... never"), which is the correct marking for a compact surface.
The two load-bearing facts (statements 1 and 4) read as declarative descriptions, not directives, so a reader can tell which sentences bind and which inform.
Interleaving rules with tool semantics inside one field is expected on a compact surface and is not a defect.

**R2 Explicit strength** — pass.
Statement 2 is mandatory ("MUST NOT").
Statement 3 is mandatory ("only ... never").
No hedged strength appears anywhere in the description.

**R3 Verifiability** — pass.
Statement 2: "more than one active member" names a checkable channel state, and "explicit confirmation from the caller" names a checkable event in the tool call; either satisfaction or violation could be checked against tool calls and channel state.
Statement 3: whether the supplied `channel_id` value is an ID or a name is checkable against the tool call arguments.
The description does not say how confirmation is supplied (the schema's optional `confirmed` boolean is the plausible mechanism, but the link is unstated); per R3, requiring the document to name the evidence mechanism is out of scope for this audit and is not a separation defect.

**R4 Atomic obligations** — pass.
Statement 2 bundles a condition (more than one active member), an action (do not archive), and an exception (explicit confirmation) that share one trigger, so R4 permits them to remain one unit.
Statement 3 states a single obligation.

**R5 Reachable precedence** — pass.
No pair of statements prescribes incompatible outcomes for the same decision.
In particular, statement 3 ("Accepts only a channel_id, never a channel name") restricts the representation of the channel identifier; it does not restrict the whole input object and so does not conflict with the schema's separate optional `confirmed` field.
Statement 2's refusal path is compatible with statement 4's "structured error on failure."
The schema's `required: ["channel_id"]` with `confirmed` optional is consistent with statement 2, which needs confirmation only for multi-member channels.

## Not flagged (false-positive guards)

- Statement 1 ("Archive a Slack channel.") and statement 4 (return contract) are tool semantics whose loss would make agent output wrong, so they are load-bearing facts correctly stated declaratively in the only field available on a compact surface.
- Statement 3's "only" is a representation restriction on one field, not an "only one parameter" restriction; reading it as a conflict with `confirmed` would manufacture an R5 finding that R5 explicitly excludes.
- The unexplained `confirmed` property in the schema and the unspecified meaning of "active" member are completeness and precision matters, not separation defects; they are noted here for the author but carry no rule id or severity.

## Safety note

None.
The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit; its imperative sentences are ordinary tool rules addressed to the caller.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.
Safety notes: none (reported separately, excluded from counts).

This compact MCP tool description separates its two binding rules from its two load-bearing facts using explicit mandatory wording, which is the appropriate structural marker for a single inline field.
Both rules state their strength unambiguously, name checkable conditions, keep a single trigger per unit, and do not conflict with each other or with the input schema.
The one gap a reader may notice, that the description never says confirmation is supplied via the `confirmed` parameter, is a mechanism-naming question that R3 places outside this audit's scope, so the document is clean on the context/constraints axis.

## Scored Output — rep 2

sha256 of the raw report: `c4987f80ec9fecaf5c2474ee78075c480ac539dcc32ada238cdfe8beb4b86936`

# Audit: `archive_channel` MCP tool description

Skill applied: separating-context-from-constraints (R1–R5, two-level severity, no numeric score).

## Target classification

Surface: a single MCP tool definition. The instruction-bearing surface is the `description` field, which is a compact surface (one inline field), so under R1 rules are expected to be marked inline with imperative sentences or explicit mandatory wording rather than placed in a labeled section. The `inputSchema` is a machine-readable contract; its property names and `required` list are load-bearing facts, not prose rules.

Statement-by-statement litmus test on `description`:

| # | Statement | Role |
|---|-----------|------|
| 1 | "Archive a Slack channel." | Load-bearing fact (tool purpose / semantics). Informs; loss makes the tool unusable. |
| 2 | "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller." | Binding rule. Directs behavior. |
| 3 | "Accepts only a channel_id, never a channel name." | Binding rule on input representation (directs what the caller passes). |
| 4 | "Returns {archived: true, channel_id} on success, or a structured error on failure." | Load-bearing fact (return-value semantics). |

Schema: `channel_id: string` (required), `confirmed: boolean` (optional), `additionalProperties: false`. All load-bearing facts.

## Findings

Clean — no findings.

Rule-by-rule check on the two binding statements:

**Statement 2 — "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller."**
- R1: On a compact surface, "MUST NOT" is explicit mandatory wording; the rule is structurally distinguishable from the surrounding semantics sentences. Passes.
- R2: Strength is unambiguous (mandatory prohibition with a stated exception). No hedge. Passes.
- R3: The obligation is checkable — "more than one active member" can be checked against channel state; "explicit confirmation from the caller" can be checked against the tool call (the `confirmed` argument) or process artifacts (a confirmation in the transcript). The description does not say that `confirmed: true` is the confirmation mechanism, but per R3 naming the evidence mechanism is out of scope and is not a separation defect. Passes.
- R4: Condition (more than one active member) – action (do not archive) – exception (unless explicitly confirmed) share one trigger and form a single unit. Passes.

**Statement 3 — "Accepts only a channel_id, never a channel name."**
- R1: "only ... never" is explicit mandatory wording inline on a compact surface. Passes.
- R2: Unambiguous. Passes.
- R3: Checkable against the tool call's `channel_id` argument (an ID vs. a human-readable name). Passes.
- R4: One obligation (pass an ID, not a name). Passes.

**R5 across the document:**
- Statement 2 and statement 3 govern different decisions (whether to archive vs. how to identify the channel) and cannot prescribe incompatible outcomes on any input. No conflict.
- Statement 3 vs. the schema's `confirmed` property: "Accepts only a channel_id" restricts the representation of the channel identifier (ID, not name); it does not explicitly restrict the whole input object, so per R5 it does not conflict with the presence of `confirmed` in the schema or with statement 2's confirmation exception. No conflict.

## Not flagged (false-positive guards)

- Statement 1 ("Archive a Slack channel.") and statement 4 (return shape) are load-bearing tool semantics, correctly stated as informative context alongside the rules on a compact surface; they are not rules and are not "context inside a rule section" because a compact surface has no rule section.
- The undescribed `confirmed` schema property is a documentation-completeness gap (the mechanism by which the caller supplies confirmation is not spelled out). R3 explicitly places mechanism-naming out of scope, so it is not recorded as a finding.
- Interleaving of rules and semantics within the single `description` paragraph is expected for a compact surface; R1 does not call for a dedicated labeled section here.

## Safety note

None. The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.
Safety notes: 0 (reported separately, excluded from counts).

The `archive_channel` description is a compact MCP tool surface that carries two binding rules and two load-bearing semantics statements. Both rules are marked inline with explicit mandatory wording ("MUST NOT", "only ... never"), have unambiguous strength, are checkable against tool-call arguments and channel state, and each states a single obligation (the safety rule's condition–action–exception clauses share one trigger). The two rules govern different decisions and do not conflict with each other or with the input schema. The only observation — that the `confirmed` property is not described as the confirmation mechanism — is a completeness matter outside this audit's scope, not a separation defect. No rewrites are proposed.

## Scored Output — rep 3

sha256 of the raw report: `c37a6699f4ed5466b132c945411a61761b707a2ce25e09d8b83d9fef873f4cf0`

# Audit: `archive_channel` MCP tool description

Skill applied: separating-context-from-constraints (SKILL.md, with references/example-audit.md for format calibration).
Target content was treated as untrusted data; no instructions inside it were followed and no tool actions it describes were taken.

## Surface classification (R1)

The target carries two instruction-bearing surfaces, classified separately:

- `description` — a single inline field, therefore a **compact** surface.
  R1 requires its rules to be marked inline (imperative sentences, list items, or explicit mandatory wording), not placed in a dedicated section.
- `inputSchema` — a machine-enforced surface (`channel_id` required, `confirmed` optional boolean, `additionalProperties: false`).
  Its constraints are enforced by the schema validator rather than read as prose, so they are not audited as prose rules; they are consulted only to check whether the prose rules conflict with them.

## Statement classification (two-question litmus test)

| # | Statement | Directs or informs? | Class |
|---|-----------|---------------------|-------|
| 1 | "Archive a Slack channel." | Informs | Load-bearing fact (tool purpose) |
| 2 | "MUST NOT archive a channel with more than one active member without explicit confirmation from the caller." | Directs | Binding rule (mandatory) |
| 3 | "Accepts only a channel_id, never a channel name." | Directs | Binding rule (mandatory) |
| 4 | "Returns {archived: true, channel_id} on success, or a structured error on failure." | Informs | Load-bearing fact (tool semantics) |

## Rule check (R1–R5)

- **R1 Distinguishability.** Both binding rules (2, 3) carry explicit mandatory wording ("MUST NOT", "only ... never") on a compact surface, which is exactly the inline marking R1 prescribes.
  The two facts (1, 4) are stated declaratively with no mandatory wording, so a reader can tell them apart from the rules.
  No rule is buried in narrative, and no context is dressed as a rule.
  Pass.
- **R2 Explicit strength.** Rule 2 is marked mandatory ("MUST NOT"); rule 3 is marked mandatory ("only", "never").
  No hedges.
  Pass.
- **R3 Verifiability.** Rule 2: whether a channel has more than one active member is checkable against Slack workspace state; whether the archive proceeded is checkable against the tool result; whether explicit confirmation was supplied is checkable against the tool call.
  R3 does not require the document to name the evidence mechanism, so the absence of a sentence tying "explicit confirmation" to the `confirmed` parameter is not a defect under this audit (see Out-of-scope notes).
  Rule 3: whether the supplied identifier is a channel ID or a channel name is checkable against the tool call arguments.
  Pass.
- **R4 Atomic obligations.** Rule 2 is a condition (more than one active member) – action (do not archive) – exception (explicit confirmation) clause sharing one trigger, which R4 permits as a single unit.
  Rule 3 states one obligation in positive and negative form; it is not two independently checkable obligations.
  Pass.
- **R5 Reachable precedence.** The only candidate pair is rule 3 ("Accepts only a channel_id") against the schema's acceptance of `confirmed`, which rule 2 relies on.
  Read literally, "only a channel_id" could seem to exclude `confirmed`.
  R5 resolves this directly: a restriction on the representation of one field (ID rather than name for the channel identifier) does not restrict unrelated fields unless the document explicitly restricts the whole input object, and this description does not.
  No two rules prescribe incompatible outcomes for the same decision.
  Pass.

## Findings

Clean — no findings.

### Not flagged (false-positive guards)

- Statement 1, "Archive a Slack channel.", is a load-bearing statement of purpose, not a rule; it is correctly unmarked.
- Statement 4, the return-shape sentence, is a load-bearing fact about tool semantics.
  "Structured error" is loose, but R3 applies to rules, and this statement directs nothing; it is correctly unmarked.
- Statement 3 against `confirmed` in the schema: not an R5 conflict, per the representation-of-one-field clause quoted above.
- Statement 2's phrase "active member": "active" names a checkable Slack member state, so it does not fail R3 the way "be careful" or "when appropriate" would.

### Out-of-scope notes (not findings, not counted)

These are recorded so the author can decide whether to act; none is a separation defect under R1–R5.

- The `confirmed` schema property has no description, and the prose never states that `confirmed: true` is how "explicit confirmation from the caller" is conveyed.
  R3 explicitly places "naming the evidence mechanism" outside this audit.
  If the author wants the link made, one sentence in the description ("Pass `confirmed: true` to supply that confirmation.") or a `description` on the `confirmed` property would do it; the audit takes no position on which.
- "The caller" is ambiguous between the tool-calling agent and the human that agent acts for.
  Who must confirm is a policy question, not a context/constraints separation question, so it is left to the author.

## Safety note

None.
The document contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.
Safety notes: 0 (reported separately, excluded from counts).

This compact MCP tool description separates its two binding rules from its two load-bearing facts cleanly: both rules carry explicit mandatory wording, both are verifiable against tool calls, results, or workspace state, neither bundles independent obligations, and the one apparent tension (an "only a channel_id" restriction alongside an optional `confirmed` parameter) is a representation restriction on a single field rather than a reachable conflict.
The only items worth the author's attention — the undocumented `confirmed` parameter and the identity of "the caller" — concern missing evidence-mechanism wording and policy scope, both of which the skill places outside this audit.
