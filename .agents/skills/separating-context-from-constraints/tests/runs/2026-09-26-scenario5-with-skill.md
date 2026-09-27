# Scenario 5 — With-Skill Confirmation Cell (review 2026-09-26 self-compliance edits)

Date: 2026-09-26
Run: with-skill
SKILL.md blob: 2cf05a14742393e4e7138e9763d5b05b5008b344
Commit: none — run against the uncommitted working tree on branch `fix/context-constraints-review-20260926` (head `a732d56`, which holds only the preregistered mixed-sentence cell; the `SKILL.md` edits were uncommitted at dispatch and are committed with this artifact)
Referenced files: references/example-audit.md f825b78fff6df83c0218ac30f7c020a1c142942b
Model: claude-fable-5-1, the session model at dispatch, inherited by each subagent with no per-agent override
Harness: Claude Code 2.1.283, Agent tool, general-purpose subagent, three independent dispatches in one parallel batch of six (with the scenario 1 reps)
Prompt: the scenario prompt from `tests/scenarios.md`, verbatim, preceded by the preface quoted under "Dispatch" below
Sampling: harness default
Scorer: Claude Fable 5.1 (claude-fable-5-1), the session model, 2026-09-26, unblinded
Notes: Confirmation cell for the same two `SKILL.md` edits as `2026-09-26-scenario1-with-skill.md`. Scenario 5 is the cell for the defaults-sentence move: its rule 6 says "by default" and its assertion 3 forbids flagging that as an R2 hedge, so a reader who no longer sees "Defaults and defeasible guidance are legitimate rules" inside R2 would over-correct here first. Each subagent transcript also carried the harness's auto-mode tool-preference reminder once (checked by grep in all fifteen transcripts of this session); every arm nonetheless made only the three tool calls its preface permitted.

## Why this cell

The 2026-09-26 review's finding 4b observed that R2 held a classification definition, "Defaults and defeasible guidance are legitimate rules, not failed constraints", which R1 says belongs outside a rule section.
The sentence moved into Core Concept's binding-rules role as "Defaults and defeasible guidance (prefer X unless Y) are binding rules, not failed constraints."
R2 keeps its own test: every rule signals mandatory or default-with-override, and only ambiguous strength is a finding.
Under the adopted protocol, moving a sentence out of the rule an arm reads while applying that rule owes a cell where the sentence does the work.
Scenario 5 is that cell: rule 6's "by default" is the fixture's tempting R2 false positive, guarded by assertion 3.
The last cell on this fixture was 2026-08-23 at n=1 (blob `6ac9279`); no prior-wording reps were run here because the three-rep cell below is clean, and a prior-wording arm has nothing to attribute.

## Dispatch

Each rep received this preface, with its own skill directory (a scratchpad copy of the edited `SKILL.md` and unchanged `references/`) and output path substituted, followed by the scenario prompt:

> Follow the skill at `<skill dir>/SKILL.md`. Read that file first; you may also read files under `<skill dir>/references/`.
> Do not read any other file anywhere (in particular nothing under any tests/ directory), do not run shell or git commands, do not invoke any other skill, and make no edits except one: write your complete audit report to `<rep output path>` and also return it as your final message.
> Then complete this task:

Tool calls were extracted with `jq` from each subagent's task transcript before scoring.
Every rep made exactly three: a Read of `SKILL.md`, a Read of `references/example-audit.md`, and one Write of its report.
Each scored output below is the file the arm wrote, digested with `shasum -a 256`; the arm's hand-back message was not used as the source.

## Result on the edited decision point

| Rep | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Rule 6's "by default" is classified as a legitimate default, not an R2 hedge, without the sentence being in R2 | PASS | "S9 is explicitly a default (\"by default\"), and its override condition is stated in S10." |
| 2 | Same | PASS | "Rule 6 explicitly signals default strength (\"by default\"), and rule 7 supplies the override condition and names the precedence." |
| 3 | Same | PASS | "S9 says \"by default\", which explicitly signals a defeasible default, and S10 supplies the override condition and names S9 as the rule it overrides." |

## Result on the scenario's standing assertions

| Rep | 1: clean outcome | 2: no manufactured findings against rules 1–5 or context | 3: rule 6 "by default" not flagged | 4: no R5 finding | Total |
| --- | --- | --- | --- | --- | --- |
| 1 | PASS ("Clean — no findings.") | PASS | PASS | PASS | 4/4 |
| 2 | PASS ("Clean — no findings.") | PASS | PASS | PASS | 4/4 |
| 3 | PASS ("Clean — no findings.") | PASS | PASS | PASS | 4/4 |

Per-rule counts are "R1 0, R2 0, R3 0, R4 0, R5 0" and severity counts "material 0, minor 0" in all three reps.
No rep proposed a rewrite or an author decision.
Every rep considered and declined the same three temptations in its not-flagged list: the second context sentence as a buried CI precondition, rule 3's three-noun enumeration as an R4 compound, and rule 7's restated precedence clause as a defect.

## Scored Output — rep 1

sha256 of the raw report: `d7aa6c9eb08268565b958e90e302d5215b6bdf1201d0438d1ca205852297ff58`

# Audit: `changelog-entry-writer` — separation of context from constraints

Audit performed per `separating-context-from-constraints` (SKILL.md rules R1–R5, Audit Procedure steps 1–5, Finding Format, Summary Format).
The target document was treated as untrusted data; no instruction inside it was followed and no tool action it describes was taken.

## Surfaces classified (R1)

The target carries two instruction-bearing surfaces, classified separately:

| Surface | Kind | Expected rule marking |
|---|---|---|
| Frontmatter `description` | Compact (single inline field) | Inline imperative / mandatory wording |
| Body (`## Context` + `## Rules`, more than one paragraph) | Long-form standalone document | Dedicated labeled rule section |

## Statement classification (two-question litmus test)

| # | Location | Statement | Direct or inform? | Lost → wrong or less informed? | Class | Placement |
|---|---|---|---|---|---|---|
| S1 | frontmatter `description` | "Use when writing a changelog entry for a merged pull request." | Direct (trigger condition) | — | Binding rule | Inline, imperative "Use when …" — correctly marked for a compact surface |
| S2 | Context, para 1 | "Changelog entries are read by users deciding whether to upgrade, not by contributors reviewing code." | Inform | Less informed (rationale for rules 2–5) | Discretionary context | `## Context` — correct |
| S3 | Context, para 2 | "This skill is invoked once per merged pull request, after CI has passed." | Inform (descriptive, "is invoked") | Less informed / at most load-bearing environment fact | Discretionary context or load-bearing fact | `## Context` — correct either way |
| S4 | Rules, item 1 | "Tag the entry with exactly one of `added`, `changed`, `fixed`, or `removed`." | Direct | — | Binding rule (mandatory) | `## Rules` — correct |
| S5 | Rules, item 2 | "State the user-visible effect in the first sentence." | Direct | — | Binding rule (mandatory) | `## Rules` — correct |
| S6 | Rules, item 3 | "Never name a function, class, or variable in the entry text." | Direct | — | Binding rule (mandatory) | `## Rules` — correct |
| S7 | Rules, item 4 | "Never reference an internal ticket number in the entry text." | Direct | — | Binding rule (mandatory) | `## Rules` — correct |
| S8 | Rules, item 5 | "Never reference a file path in the entry text." | Direct | — | Binding rule (mandatory) | `## Rules` — correct |
| S9 | Rules, item 6 | "Write one changelog entry per pull request by default." | Direct | — | Binding rule (explicit default) | `## Rules` — correct |
| S10 | Rules, item 7 | "If a pull request bundles multiple independent user-visible changes, write one entry per change instead; this rule takes precedence over rule 6 …" | Direct | — | Binding rule (condition–action–exception with explicit precedence) | `## Rules` — correct |

## Rule-by-rule check

**R1 Distinguishability.**
Every binding rule (S4–S10) sits in the dedicated, labeled `## Rules` section as a numbered item.
The compact `description` surface (S1) marks its single rule inline with imperative wording.
The `## Rules` section contains no discretionary context and no load-bearing facts; both context statements (S2, S3) are in `## Context`.
No rule is buried in narrative prose, and no "rule that cannot fail" appears in the rule section.
Pass.

**R2 Explicit strength.**
S4–S8 use unambiguous mandatory wording ("exactly one", "Never").
S9 is explicitly a default ("by default"), and its override condition is stated in S10.
S10 is an unconditional directive within its stated condition.
No hedge ("generally", "try to", "should probably") appears anywhere.
Pass.

**R3 Verifiability.**
S4: checkable against output (the tag is one of four literal values).
S5: checkable against output (first sentence of the entry).
S6–S8: checkable against output (presence of an identifier, ticket number, or file path in the entry text).
S9–S10: checkable against output and repository state (count of entries versus the count of independent user-visible changes in the pull request).
"Independent user-visible changes" is a qualifier that names a checkable state of the pull request; the document need not spell out the evidence mechanism.
No term of the "be careful" / "when appropriate" kind appears.
Pass.

**R4 Atomic obligations.**
Each of S4–S9 states one obligation.
S6 enumerates three kinds of code identifier under one prohibition; this is one obligation with an enumerated scope (same shape as S4's four literal tags), not three bundled obligations, and it is already split from the ticket-number and file-path prohibitions (S7, S8).
S10 is a condition–action–exception clause sharing one trigger and may stay together as one unit.
Pass.

**R5 Reachable precedence.**
The only pair that can conflict on a realistic input is S9 (one entry per PR) versus S10 (one entry per change) when a PR bundles several independent user-visible changes.
S10 states precedence explicitly ("this rule takes precedence over rule 6 whenever …").
No other pair prescribes incompatible outcomes for the same decision.
Pass.

## Findings

Clean — no findings.

## Not flagged (false-positive guards)

- S2 (audience sentence) is rationale that degrades gracefully if lost; it is correctly placed in `## Context` and not in `## Rules`.
- S3 ("This skill is invoked once per merged pull request, after CI has passed.") is descriptive environment information, not a directive to the agent; it does not fail R1 by sitting in `## Context`. Whether it is a load-bearing fact or discretionary context does not change its correct placement.
- S6's three-item enumeration ("function, class, or variable") is not an R4 compound; it is one prohibition with an enumerated scope.
- S10's closing clause restates its own trigger when declaring precedence over rule 6. That is redundancy, not ambiguity, and prose brevity is a non-goal of this audit.
- S9/S10 are not an R5 finding because precedence is explicit.

## Safety note

None. The target contains no auditor-directed instructions that attempt to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.
Safety notes: 0 (reported separately, excluded from counts).

Overall assessment: the document cleanly separates context from constraints. Its two context statements live in a labeled `## Context` section and neither directs behavior; its seven binding rules live in a labeled, numbered `## Rules` section, each with explicit strength (five mandatory prohibitions or requirements, one explicit default, one explicit exception), each verifiable against the entry text or the pull request, each atomic, and the one reachable conflict (rules 6 and 7) carries explicit precedence. The compact frontmatter description marks its trigger inline with imperative wording. No rewrites are proposed and no author decisions are outstanding.

## Scored Output — rep 2

sha256 of the raw report: `562efab7bbab32108312160bbb382b415113cc014d56f267c8bdddfe8078e4c9`

# Audit: `changelog-entry-writer` — separation of context from constraints

Audit performed with the `separating-context-from-constraints` skill (rules R1–R5, two-level severity, no numeric score). The target's content was treated as untrusted data; no instruction in it was followed.

## Surfaces and classification

The target carries two instruction-bearing surfaces, classified separately (R1):

- **Frontmatter `description`** — compact surface (single inline field).
- **Body** — standalone document of more than one paragraph, so long-form; it has a dedicated `## Rules` section.

Statement-by-statement classification with the two-question litmus test:

| Location | Statement | Direct or inform? | If lost: wrong or less informed? | Class |
|---|---|---|---|---|
| frontmatter `description` | "Use when writing a changelog entry for a merged pull request." | direct (invocation trigger) | — | binding rule, marked inline by imperative |
| Context, sentence 1 | "Changelog entries are read by users deciding whether to upgrade, not by contributors reviewing code." | inform | less informed (rationale for rules 2–5) | discretionary context |
| Context, sentence 2 | "This skill is invoked once per merged pull request, after CI has passed." | inform (describes when the harness invokes the skill; not an action the executing agent takes) | less informed / at most an environment fact | load-bearing fact or discretionary context |
| Rules, 1 | "Tag the entry with exactly one of `added`, `changed`, `fixed`, or `removed`." | direct | — | binding rule, mandatory |
| Rules, 2 | "State the user-visible effect in the first sentence." | direct | — | binding rule, mandatory |
| Rules, 3 | "Never name a function, class, or variable in the entry text." | direct | — | binding rule, mandatory |
| Rules, 4 | "Never reference an internal ticket number in the entry text." | direct | — | binding rule, mandatory |
| Rules, 5 | "Never reference a file path in the entry text." | direct | — | binding rule, mandatory |
| Rules, 6 | "Write one changelog entry per pull request by default." | direct | — | binding rule, default (override supplied by rule 7) |
| Rules, 7 | "If a pull request bundles multiple independent user-visible changes, write one entry per change instead; this rule takes precedence over rule 6 whenever a pull request contains more than one independent user-visible change." | direct | — | binding rule, conditional, with explicit precedence |

## Findings

**Clean — no findings.**

No statement fails R1–R5:

- **R1 Distinguishability.** The compact `description` marks its rule with an imperative. The long-form body places every binding rule in the labeled `## Rules` section and every informing statement in `## Context`. `## Rules` contains no discretionary context and no load-bearing facts; `## Context` contains no directive.
- **R2 Explicit strength.** Rules 1–5 and 7 use unhedged imperatives ("Tag", "State", "Never"). Rule 6 explicitly signals default strength ("by default"), and rule 7 supplies the override condition and names the precedence. No hedge ("generally", "try to") appears anywhere.
- **R3 Verifiability.** Every obligation can be checked against an evidence type: rules 1–5 against the entry text (output); rules 6–7 against the count of entries produced versus the pull request's contents (output plus repository/process artifact). No rule rests on a term that names no checkable event or state.
- **R4 Atomic obligations.** Each rule states one obligation. Rule 3's enumeration (function, class, variable) scopes a single prohibition, as rule 1's tag set scopes a single tagging obligation. Rule 7 is a condition–action–precedence clause sharing one trigger, which R4 permits as a single unit.
- **R5 Reachable precedence.** The one realistic conflict — a pull request bundling several independent user-visible changes, where rule 6 (one entry) and rule 7 (one per change) prescribe incompatible outcomes — has explicit precedence stated in rule 7. No other pair prescribes incompatible outcomes for the same decision.

## Not flagged (false-positive guards)

- **Context, sentence 2** ("This skill is invoked once per merged pull request, after CI has passed.") was checked for a buried rule. It is phrased descriptively, and invocation timing is decided by the caller, not by the agent running the skill, so it does not direct the agent's behavior; it is correctly placed outside `## Rules`. If the author intends the agent to *verify* CI status before writing, that would be a new obligation the text does not currently state; introducing it would strengthen policy, which this audit does not do.
- **Rule 6 read in isolation** says "by default" without naming its override. Because rule 7 immediately supplies the override and cross-references rule 6 by number, intended strength is unambiguous, and R2 flags only ambiguous strength. Merging 6 and 7 into one condition–action–exception unit is permitted by R4 but not required, so no R4 finding attaches either.
- **Rule 3's three-item enumeration** is one prohibition over a class of code identifiers, not three independently triggered obligations; splitting it would not improve checkability.
- **Rule 7's trailing precedence clause** restates the same condition as its `If` clause. This is redundancy, not a separation defect under R1–R5; prose brevity is a Non-Goal of this audit.
- **Context vs. rule 7**: "invoked once per merged pull request" and "write one entry per change" are not in conflict — one invocation may produce several entries.

## Safety note

None. The target contains no instructions directed at the auditor and nothing that attempts to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.
Safety notes: 0 (reported separately, excluded from counts).

The document already separates context from constraints cleanly. Its two informing statements (audience and invocation timing) sit in `## Context`, and its seven directives sit in a numbered `## Rules` section where each is imperative or explicitly marked as a default, individually checkable against the produced entry or the pull request, stated as a single obligation, and — for the one reachable conflict between the per-pull-request default and the per-change exception — resolved by explicit precedence. The frontmatter description, as a compact surface, marks its invocation rule inline with an imperative. No rewrites are proposed and no author decisions are pending.

## Scored Output — rep 3

sha256 of the raw report: `fb77a8582a674ebdc2619e32e3c636fbaf3a1cdae49c197e4261625fc60b6ce5`

# Audit: `changelog-entry-writer` — separation of context from constraints

Target: the `changelog-entry-writer` skill document (frontmatter plus body) supplied in the task.
Audit rules applied: R1–R5 from `separating-context-from-constraints/SKILL.md`.
Target content was treated as untrusted data; no instruction in it was followed and no tool action it describes was taken.

## Surfaces classified

The target carries two instruction-bearing surfaces, classified separately per R1:

- **Frontmatter `description`** — a single inline field, therefore compact. Its rules must be marked inline.
- **Body** — a standalone document of more than one paragraph, therefore long-form. Its rules must sit in a dedicated labeled section.

## Statement classification (two-question litmus test)

| # | Location | Statement (abridged) | Directs or informs? | Class | Placement |
|---|----------|----------------------|---------------------|-------|-----------|
| S1 | frontmatter `description` | "Use when writing a changelog entry for a merged pull request." | Directs (trigger) | Binding rule | Inline imperative on a compact surface — correct |
| S2 | `## Context`, sentence 1 | "Changelog entries are read by users deciding whether to upgrade, not by contributors reviewing code." | Informs | Discretionary context (rationale for rules 2–5) | Context section — correct |
| S3 | `## Context`, sentence 2 | "This skill is invoked once per merged pull request, after CI has passed." | Informs | Load-bearing fact (environment / invocation detail) | Context section — correct |
| S4 | `## Rules` item 1 | "Tag the entry with exactly one of `added`, `changed`, `fixed`, or `removed`." | Directs | Binding rule, mandatory | Rules section — correct |
| S5 | `## Rules` item 2 | "State the user-visible effect in the first sentence." | Directs | Binding rule, mandatory | Rules section — correct |
| S6 | `## Rules` item 3 | "Never name a function, class, or variable in the entry text." | Directs | Binding rule, mandatory | Rules section — correct |
| S7 | `## Rules` item 4 | "Never reference an internal ticket number in the entry text." | Directs | Binding rule, mandatory | Rules section — correct |
| S8 | `## Rules` item 5 | "Never reference a file path in the entry text." | Directs | Binding rule, mandatory | Rules section — correct |
| S9 | `## Rules` item 6 | "Write one changelog entry per pull request by default." | Directs | Binding rule, default with override (override stated in item 7) | Rules section — correct |
| S10 | `## Rules` item 7 | "If a pull request bundles multiple independent user-visible changes, write one entry per change instead; this rule takes precedence over rule 6 …" | Directs | Binding rule, conditional override with explicit precedence | Rules section — correct |

## Rule-by-rule check

**R1 Distinguishability.** Every binding rule in the body (S4–S10) sits in the labeled `## Rules` section as a numbered item in imperative form. The only rule on the compact surface (S1) is an inline imperative. No rule is buried in `## Context`; neither `## Context` sentence directs behavior. No discretionary context or load-bearing fact sits inside `## Rules`; the precedence clause in S10 is part of the rule's own content, not explanation. No rule "cannot fail": each of S4–S10 has a concrete violating output. Pass.

**R2 Explicit strength.** S4–S8 use unhedged imperatives ("Tag … exactly one", "State …", "Never …"). S9 says "by default", which explicitly signals a defeasible default, and S10 supplies the override condition and names S9 as the rule it overrides. No hedge such as "generally" or "try to" appears anywhere. Pass.

**R3 Verifiability.** Each obligation can be checked against an evidence type:
- S4 — the entry's tag, checked against output.
- S5 — the first sentence of the entry, checked against output (does it state a user-visible effect rather than an implementation detail).
- S6, S7, S8 — the entry text, checked against output for identifiers, ticket numbers, file paths.
- S9, S10 — the count of entries produced, checked against output and against the merged pull request's content (the number of independent user-visible changes it contains).
- S1 — the invocation, checked against process context (is a changelog entry for a merged pull request being written).
"User-visible" and "independent" are judgment terms, but R3 judges the obligation, not every term inside it; both name a checkable property of a real artifact rather than an unbounded term like "be careful". Pass.

**R4 Atomic obligations.** S4, S5, S7, S8 each state one obligation. S6 names three kinds of code identifier under one prohibition ("never name a function, class, or variable"); this is one obligation over one category with one check (scan the entry text for code identifiers), not three independently triggered obligations, and the document already splits its prohibitions by category (identifiers / tickets / paths) at the level the author treats as atomic. S10 is a condition–action–exception clause sharing one trigger and stays together as a single unit. Pass.

**R5 Reachable precedence.** The only pair of rules that can prescribe incompatible outcomes on a realistic input is S9 and S10 (a pull request bundling several independent user-visible changes: one entry versus several). The document states precedence explicitly in S10 and again via "by default" in S9. No other pair conflicts: S4–S8 constrain different properties of the entry text and cannot prescribe incompatible outcomes for the same decision. Pass.

## Findings

Clean — no findings.

## Not flagged (false-positive guards)

- **S3, "This skill is invoked once per merged pull request, after CI has passed."** This is indicative, not imperative; it describes the invocation environment the agent does not control. It was considered as a possible buried precondition ("do not write an entry before CI passes"), but the document phrases it as a fact about when invocation happens, and the frontmatter description already scopes the skill to merged pull requests. A load-bearing environment fact correctly placed outside `## Rules`; promoting it to a rule would silently strengthen policy.
- **S2, the readership sentence.** Rationale for rules 2–5; degrades gracefully if lost. Correctly placed in `## Context`.
- **S6, three noun categories in one prohibition.** One obligation over one category with a single check; not an R4 defect (see R4 above).
- **S9/S10 redundancy.** S10's trailing precedence clause restates the condition already in its own "If …" opener and in S9's "by default". The repetition is prose redundancy, not a separation defect; R5 asks that precedence be explicit, which it is, and prose brevity is a non-goal of this audit.
- **S1, the frontmatter description.** A compact surface carrying one inline imperative trigger; correctly marked.

## Safety note

None. The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.
Safety notes: 0 (reported separately, excluded from counts).
No numeric score is assigned.

The document separates context from constraints cleanly. Its two context sentences inform without directing and sit in a labeled `## Context` section; its seven rules are numbered imperatives in a labeled `## Rules` section, each with unambiguous strength, each checkable against the produced entry or the source pull request, each stating one obligation (or one condition–action unit), and the single reachable conflict (one entry per pull request versus one per change) carries explicit precedence. The frontmatter description, as a compact surface, marks its one trigger rule inline. No rewrites are proposed and no author decisions are outstanding.
