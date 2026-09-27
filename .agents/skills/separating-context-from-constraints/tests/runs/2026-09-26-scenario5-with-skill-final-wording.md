# Scenario 5 — With-Skill Confirmation Cell (final wording after Copilot review)

Date: 2026-09-26
Run: with-skill
SKILL.md blob: 9651c25f77a769854d64bd23803bbb35f5a33bd8
Commit: none — run against the uncommitted working tree on branch `fix/context-constraints-review-20260926` (head `e76cd7a`); the only uncommitted change was the one-line Copilot review fix to `SKILL.md`, committed with this artifact
Referenced files: references/example-audit.md f825b78fff6df83c0218ac30f7c020a1c142942b
Model: claude-fable-5-1, the session model at dispatch, inherited by each subagent with no per-agent override
Harness: Claude Code 2.1.283, Agent tool, general-purpose subagent, three independent dispatches in one parallel batch of six (scenarios 1 and 5)
Prompt: the scenario prompt from `tests/scenarios.md`, verbatim, preceded by the preface quoted under "Dispatch" below
Sampling: harness default
Scorer: Claude Fable 5.1 (claude-fable-5-1), the session model, 2026-09-26, unblinded
Notes: Rerun of `2026-09-26-scenario5-with-skill.md` on the final blob after the Copilot review fix. The defaults sentence this cell exists for is byte-identical across `2cf05a1` and `9651c25`; the rerun is run anyway so that the shipped blob has its own cell. Each subagent transcript also carried the harness's auto-mode tool-preference reminder once (checked by grep in all fifteen transcripts of this session); every arm nonetheless made only the three tool calls its preface permitted.

## Why this cell

Copilot's review of PR #182 noted that the replacement line "The two-question litmus test that classifies a statement:" is a noun phrase, not a sentence.
It became "The two-question litmus test classifies a statement:", the same content as a declarative sentence.
That changes the blob the earlier 2026-09-26 cells cite (`2cf05a1`), so both confirmation cells were rerun on the final blob rather than carried across by argument.

## Dispatch

Each rep received this preface, with its own skill directory (a scratchpad copy of the final `SKILL.md` and unchanged `references/`) and output path substituted, followed by the scenario prompt:

> Follow the skill at `<skill dir>/SKILL.md`. Read that file first; you may also read files under `<skill dir>/references/`.
> Do not read any other file anywhere (in particular nothing under any tests/ directory), do not run shell or git commands, do not invoke any other skill, and make no edits except one: write your complete audit report to `<rep output path>` and also return it as your final message.
> Then complete this task:

Tool calls were extracted with `jq` from each subagent's task transcript before scoring.
Every rep made exactly three: a Read of `SKILL.md`, a Read of `references/example-audit.md`, and one Write of its report.
Each scored output below is the file the arm wrote, digested with `shasum -a 256`; the arm's hand-back message was not used as the source.

## Result on the edited decision point

| Rep | Question | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Rule 6's "by default" is read as a legitimate default with the defaults sentence outside R2 | PASS | "Rule 6's "by default" does not leave its strength unclear. It is an explicit default, and rule 7 supplies the override and its precedence." |
| 2 | Rule 6's "by default" is read as a legitimate default with the defaults sentence outside R2 | PASS | "Rule 6 is explicitly a default ("by default"), and rule 7 states its override condition." |
| 3 | Rule 6's "by default" is read as a legitimate default with the defaults sentence outside R2 | PASS | "Rule 6 says "by default", and rule 7 gives its override condition. None of them is hedged." |

## Result on the scenario's standing assertions

| Rep | 1: clean outcome | 2: no manufactured findings against rules 1–5 or context | 3: rule 6 "by default" not flagged | 4: no R5 finding | Total |
| --- | --- | --- | --- | --- | --- |
| 1 | PASS ("Clean — no findings.") | PASS | PASS | PASS | 4/4 |
| 2 | PASS ("Clean: no findings.") | PASS | PASS | PASS | 4/4 |
| 3 | PASS ("Clean — no findings.") | PASS | PASS | PASS | 4/4 |

Per-rule counts are "R1 0, R2 0, R3 0, R4 0, R5 0" and severity counts "material 0, minor 0" in all three reps.
No rep proposed a rewrite or an author decision.

## Scored Output — rep 1

sha256 of the raw report: `7f2234067d59b320a93f25eb2ad81973e915242eaa22a0ca4e175621f0bf3488`

# Audit: changelog-entry-writer

Line numbers count from the opening `---` of the target document as line 1.

## Outcome

Clean — no findings.

## Surface classification (R1)

- Frontmatter `description` (line 3) is a compact surface. It states only the trigger condition ("Use when writing a changelog entry for a merged pull request."), which is not a rule. It needs no inline rule marking.
- The body (lines 6–21) is a standalone long-form surface: more than one paragraph under separate headings. Its rules sit in a dedicated labeled `## Rules` section, as R1 requires.

## Statement classification

| Line | Statement | Class | Placement |
|---|---|---|---|
| 10 | "Changelog entries are read by users deciding whether to upgrade, not by contributors reviewing code." | Discretionary context (explains why rules 2–5 exist) | `## Context`, correct |
| 11 | "This skill is invoked once per merged pull request, after CI has passed." | Load-bearing fact (describes how the skill is invoked; it tells the agent something, it does not direct it) | `## Context`, correct |
| 15 | Rule 1, tag with exactly one of four values | Binding rule, mandatory | `## Rules`, correct |
| 16 | Rule 2, user-visible effect in first sentence | Binding rule, mandatory | `## Rules`, correct |
| 17 | Rule 3, never name a function, class, or variable | Binding rule, mandatory | `## Rules`, correct |
| 18 | Rule 4, never reference an internal ticket number | Binding rule, mandatory | `## Rules`, correct |
| 19 | Rule 5, never reference a file path | Binding rule, mandatory | `## Rules`, correct |
| 20 | Rule 6, one entry per pull request by default | Binding rule, a default that can be overridden | `## Rules`, correct |
| 21 | Rule 7, one entry per independent change; takes precedence over rule 6 | Binding rule, a condition and action with stated precedence | `## Rules`, correct |

## Rule-by-rule check

- **R1 Distinguishability:** passes. Every binding rule is a numbered item in `## Rules`. The rules section holds no context or facts. The two context sentences sit under `## Context`. Every rule can fail, so none is context in disguise.
- **R2 Explicit strength:** passes. Rules 1–5 are unhedged. "exactly one", the imperatives and "Never" mark them as mandatory. Rule 6 says "by default", so it is openly a default that can be overridden, and rule 7 names the override. Nothing uses a hedge like "generally" or "try to".
- **R3 Verifiability:** passes. Each rule can be checked against the entry text and the pull request:
  - Rule 1: count the tags and check each against the four allowed values.
  - Rule 2: check the first sentence.
  - Rules 3–5: scan the entry text for identifiers, ticket numbers and paths.
  - Rules 6–7: compare the number of entries with the number of independent user-visible changes in the pull request.

  "Independent user-visible change" is a judgment call, but it names a state of the pull request that can be checked. It is not an empty term like "when appropriate".
- **R4 Atomic obligations:** passes. The ticket-number and file-path bans are separate rules (4 and 5). Rule 7's condition, action and precedence clause share one trigger (a pull request with more than one independent user-visible change), so they can stay together as one unit.
- **R5 Reachable precedence:** passes. Rules 6 and 7 really do conflict on a realistic input: a pull request that bundles several changes. Rule 7 states that it wins "whenever a pull request contains more than one independent user-visible change". No other pair of rules gives incompatible outcomes for the same decision.

## Not flagged (false-positive guards)

- Line 11 is an invocation fact. It is not a hidden rule such as "only run after CI passes". It describes the environment and gives the agent no instruction, so it belongs in `## Context`.
- Line 17 (rule 3) lists three kinds of identifier, but it is one ban with one check: the entry text names no code identifier. Splitting it into three rules would be over-correction, not an R4 fix. Rules 4 and 5 being split out does not make rule 3 a compound rule.
- Rule 6's "by default" does not leave its strength unclear. It is an explicit default, and rule 7 supplies the override and its precedence.

## Safety note

None. The target contains no instructions aimed at the auditor.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.

This document keeps its rules and context cleanly apart. Two short context sentences (why the entries exist, and when the skill runs) sit under `## Context`. Seven numbered rules sit under `## Rules`, and the rules section holds nothing else. Each rule states its strength without hedging and can be checked against the entry text or the pull request. The prohibitions are stated separately. The one real conflict, one entry per pull request versus a pull request with several independent changes, is settled by an explicit precedence clause in rule 7. No rewrite is needed.

## Scored Output — rep 2

sha256 of the raw report: `feb1f8b0a4615ed24bb901c82b5785170d5ee34caf2baa40dcdd9ab0123f8a44`

# Audit: changelog-entry-writer

Line numbers count from the opening `---` of the target as line 1.

## Surface classification (R1)

- Frontmatter `description` (line 3): compact surface. It states only the trigger condition ("Use when writing a changelog entry for a merged pull request.") and carries no binding rules, so there is nothing that needs inline marking.
- Body (lines 6-21): standalone long-form document with more than one paragraph. Its rules sit in a dedicated labeled section (`## Rules`, lines 13-21), which is what R1 asks for.

## Statement classification

| Line | Statement (abridged) | Role |
|---|---|---|
| 3 | "Use when writing a changelog entry for a merged pull request." | Trigger condition (compact surface) |
| 10 | "Changelog entries are read by users deciding whether to upgrade, not by contributors reviewing code." | Discretionary context (the reason for rules 2-5) |
| 11 | "This skill is invoked once per merged pull request, after CI has passed." | Load-bearing fact (invocation environment) |
| 15 | Rule 1: tag with exactly one of `added`/`changed`/`fixed`/`removed` | Binding rule, mandatory |
| 16 | Rule 2: state the user-visible effect in the first sentence | Binding rule, mandatory |
| 17 | Rule 3: never name a function, class, or variable | Binding rule, mandatory |
| 18 | Rule 4: never reference an internal ticket number | Binding rule, mandatory |
| 19 | Rule 5: never reference a file path | Binding rule, mandatory |
| 20 | Rule 6: one entry per pull request by default | Binding rule, default |
| 21 | Rule 7: one entry per independent change when a PR bundles several; takes precedence over rule 6 | Binding rule, override with explicit precedence |

## Findings

Clean: no findings.

## Rule-by-rule check

- **R1 Distinguishability:** passes. Every binding rule is a numbered item under `## Rules`. The `## Rules` section contains only directives, and the two informative statements (lines 10-11) are under `## Context`. No rule is buried in the context prose.
- **R2 Explicit strength:** passes. Rules 1-5 use unhedged imperatives or "Never". Rule 6 is explicitly a default ("by default"), and rule 7 states its override condition. There are no hedges such as "generally" or "try to".
- **R3 Verifiability:** passes. Each obligation can be checked against the entry text: the tag count and tag set (rule 1), what the first sentence says (rule 2), whether identifiers, ticket numbers, or file paths appear (rules 3-5), and how many entries were written compared with how many independent user-visible changes the pull request contains (rules 6-7). "User-visible" and "independent" require judgment, but they refer to states that can be checked against the pull request and the output. Neither is a term like "when appropriate" that names nothing checkable.
- **R4 Atomic obligations:** passes. The three prohibitions are already split into rules 3, 4, and 5. Rule 3 lists three kinds of code identifier inside a single prohibition, which counts as one obligation. Rule 7 is one condition-action unit with a precedence clause attached, which R4 allows to stay together.
- **R5 Reachable precedence:** passes. The one conflict that can actually occur, rule 6 versus rule 7 on a pull request with several independent user-visible changes, has its precedence stated explicitly in rule 7.

## Not flagged (false-positive guards)

- **Line 10 (audience statement):** this is context. It gives the reason for rules 2-5 and does not direct behavior itself. It is correctly outside `## Rules`.
- **Line 11 ("invoked once per merged pull request, after CI has passed"):** this is a fact about how the skill is invoked. The harness controls invocation, not the agent. It does not create a hidden precondition rule for the agent, so it is correctly placed in `## Context`. If the author actually meant the agent to check CI status before writing an entry, that would be a new rule. Adding it would change policy, and the auditor does not infer it.
- **Rule 2 vs rule 3:** these do not conflict. A user-visible effect can be described without naming a function, class, or variable. Rule 2 never requires naming one, so the two rules never prescribe incompatible outcomes for the same decision.
- **Rule 1 vs rule 7:** these do not conflict. When rule 7 splits a pull request into several entries, rule 1 applies to each entry separately.
- **Rule 7's repeated condition:** rule 7 states its trigger twice, first as "If a pull request bundles multiple independent user-visible changes" and then as "whenever a pull request contains more than one independent user-visible change". The two phrasings mean the same thing and do not create ambiguity about strength or scope. Trimming the repetition is a prose-quality edit, which is outside this audit's scope.

## Safety note

None. The target contains no instructions aimed at the auditor.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.

This document already separates context from constraints the way this audit checks for. The body keeps its background (the audience for the entries and the invocation point) in a labeled `## Context` section. Every binding rule is a separate, numbered item in `## Rules`, with no background mixed in. Each rule's strength is clear: five mandatory rules, one default, and one override. Each obligation can be checked against the written entry and the pull request. The only reachable conflict (default single entry versus one entry per change for bundled changes) has explicit precedence. The frontmatter description is a compact trigger statement with no embedded rules. No rewrites are needed.

## Scored Output — rep 3

sha256 of the raw report: `14e70b915dce4cb884c4b36ae2b95328ce7639efea3f40b9276cfab612c93356`

# Audit: changelog-entry-writer

Target: the `changelog-entry-writer` skill document supplied inline.
Line numbers count from the opening frontmatter `---` as line 1 (rules 1–7 are lines 15–21).

## Surface classification (R1)

- **Frontmatter `description` (line 3)** is a compact surface. Its one sentence, "Use when writing a changelog entry for a merged pull request.", is an imperative trigger condition. Its rule is marked inline, which is what R1 asks of a compact surface.
- **Body (lines 6–21)** is a standalone document of more than one paragraph, so it counts as long-form. It has a dedicated labeled `## Rules` section and a separate `## Context` section, as R1 requires.

## Statement classification

| Line | Statement | Class |
|---|---|---|
| 3 | "Use when writing a changelog entry for a merged pull request." | Binding rule (trigger condition), inline on a compact surface |
| 10 | "Changelog entries are read by users deciding whether to upgrade, not by contributors reviewing code." | Context: audience rationale behind rules 2–5. It informs behavior and does not direct it. |
| 11 | "This skill is invoked once per merged pull request, after CI has passed." | Load-bearing fact about when the skill is invoked. It informs behavior and does not direct it. |
| 15 | Rule 1: tag with exactly one of `added`, `changed`, `fixed`, `removed` | Binding rule: mandatory, closed set, checkable against output |
| 16 | Rule 2: state the user-visible effect in the first sentence | Binding rule: mandatory, checkable against output |
| 17 | Rule 3: never name a function, class, or variable | Binding rule: mandatory, checkable against output |
| 18 | Rule 4: never reference an internal ticket number | Binding rule: mandatory, checkable against output |
| 19 | Rule 5: never reference a file path | Binding rule: mandatory, checkable against output |
| 20 | Rule 6: one entry per pull request "by default" | Binding rule: a default, with the override given in rule 7 |
| 21 | Rule 7: one entry per change when a PR bundles independent user-visible changes, with explicit precedence over rule 6 | Binding rule: condition, action, and precedence under one trigger |

## Findings

Clean — no findings.

Every rule was checked:

- **R1:** Every binding rule sits in `## Rules` or is marked inline on the compact description. Nothing in `## Rules` is context or a load-bearing fact. None of the rules is incapable of failing.
- **R2:** Rules 1–5 and 7 use plain imperatives or "never", so they are mandatory. Rule 6 says "by default", and rule 7 gives its override condition. None of them is hedged.
- **R3:** Each obligation can be checked against the changelog entry itself: the tag, the first sentence, whether any identifier, ticket number, or file path appears, and how many entries there are. Rule 7's condition is "independent user-visible changes". Whether it applies can be checked against the pull request's changes, which is repository state, even though the document does not say how to check it.
- **R4:** Rules 3–5 already split the three bans into separate items. Rule 7 keeps its condition, action, and precedence clause together, but all three share one trigger, which R4 allows.
- **R5:** The one pair of rules that can actually conflict is rule 6 and rule 7, on a pull request that bundles several user-visible changes. The document states the winner explicitly: "this rule takes precedence over rule 6 whenever a pull request contains more than one independent user-visible change."

## Not flagged (false-positive guards)

- **Line 10 (audience sentence):** This is rationale for rules 2–5. It informs behavior rather than directing it, so it belongs in `## Context`, where it already is. It is not a rule hidden in the prose.
- **Line 11 (invocation sentence):** This describes when the skill runs (once per merged PR, after CI passes). It is a fact about the environment, not a directive to the agent, so it is correctly kept out of `## Rules`.
- **Rule 7's restated trigger:** Rule 7 states its condition twice, once at the start and again in the precedence clause. That is wordiness, which is a prose-quality issue outside this audit's scope. It is not context mixed into a rule. The clause is binding and does the work R5 asks for.
- **Rule 2 against rules 3 and 5:** A user-visible effect is sometimes naturally described with an identifier or a path, such as a renamed public API or a moved config file. Rule 2, though, only requires the first sentence to state the effect. It does not require naming the identifier or path, so an entry can always satisfy all three rules at once. The rules never require incompatible outcomes for the same decision, so under R5 there is no conflict to resolve.
- **Rule 1 against rule 7:** When one pull request produces several entries, each entry gets exactly one tag. The two rules work together and do not conflict.
- **Frontmatter description:** A single-sentence trigger condition on a compact surface is correctly marked inline. It needs no labeled rules section.

## Safety note

None. The target contains no instructions aimed at the auditor.

## Summary

Counts per rule: R1 0, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 0, minor 0.
Safety notes: 0 (not included in the counts).

The document separates context from constraints cleanly. The two sentences of background and invocation facts sit in a labeled `## Context` section. The seven binding rules sit in a numbered `## Rules` section with no explanation mixed in. Each rule is stated once, is either clearly mandatory or clearly a default, and can be checked against the changelog entry. The only conflict that can actually arise, between the one-entry default and the multiple-change override, is settled by an explicit precedence statement in rule 7. The frontmatter description is a single inline trigger condition, which is right for a compact surface. No rewrites are needed.
