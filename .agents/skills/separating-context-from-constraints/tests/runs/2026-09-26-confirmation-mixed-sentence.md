# Mixed Sentence — Confirmation Cell (prior wording)

Date: 2026-09-26
Run: with-skill
SKILL.md blob: 713c6967362667a405048a7e75d04f18c329804c
Commit: `d709291` (main at dispatch); `SKILL.md` was written to the session scratchpad with `git show main:separating-context-from-constraints/SKILL.md`, and `references/example-audit.md` was copied beside it unchanged
Referenced files: references/example-audit.md f825b78fff6df83c0218ac30f7c020a1c142942b
Model: claude-fable-5-1, the session model at dispatch, inherited by each subagent with no per-agent override
Harness: Claude Code 2.1.283, Agent tool, general-purpose subagent, three independent dispatches in one parallel batch
Prompt: the fixture below, verbatim, preceded by the preface quoted under "Dispatch" below
Sampling: harness default
Scorer: Claude Fable 5.1 (claude-fable-5-1), the session model, 2026-09-26, unblinded
Notes: this is a confirmation cell, not a scenario. The fixture is not in `tests/scenarios.md` and was written for this cell. It is the known-positive probe for a proposed wording change, so it runs on the PRIOR wording first; the preregistration below says when the wording ships and when it is declined. Each subagent transcript also carried the harness's auto-mode tool-preference reminder once (checked by grep in all fifteen transcripts of this session); every arm nonetheless made only the three tool calls its preface permitted.

## Why this cell

The 2026-09-26 review (`review-20260926.md`, finding 2) observes that Core Concept assigns each *statement* one of three roles but never says what to do with a sentence that pairs an obligation with its rationale, and that Finding Format's "one finding per statement" therefore leaves extraction and consolidation undefined for such sentences.
The review calls the result unstable.
The archive does not show instability: the 2026-09-14 scenario 1 cell handled the fixture's mixed sentence ("must never exceed 72 characters, since several terminal-based git tools…") the same way in 3/3 reps — one R1 finding, the whole sentence quoted, the rewrite separating the obligation from the rationale.
That fixture only has the mixed sentence buried in context.
It does not exercise the other shape a clause-level unit would touch: a correctly placed rule inside `## Rules` that carries its own rationale clause, where a clause-level reading could produce a new minor R1 finding (context inside the rule section) that the current wording does not induce.

This cell settles whether the wording is needed before it is written into `SKILL.md`, per the S19/S21 precedent in the adopted protocol: a wording that the current text already induces is declined as a measured no-change-needed outcome.

## Fixture

```markdown
# release-notes-bot

## Context

Release notes are generated from merged pull requests once a week.
Every entry must name the affected component first, because the support team searches the notes by component.
The bot was moved off the legacy pipeline in 2025.

## Rules

- Never include a ticket number in an entry, since customers cannot open the tracker.
- Tag each entry with exactly one of `added`, `changed`, or `fixed`.
```

Planted (D1): line 6, the component-first sentence — a binding rule buried in `## Context` with its rationale attached in the same sentence.
Probe (P1): line 10, the ticket-number rule — correctly placed in `## Rules`, with a rationale clause attached. Neither planted nor protected; the cell records what each arm does with it.
Protected: line 5 (schedule fact), line 7 (history), line 11 (clean rule).

Correction, added after scoring (Codex cross-check of PR #182): the two `## Rules` references above miscount the blank line after the heading. P1 is line 11 and the protected tagging rule is line 12; lines 5, 6, and 7 are correct as written. Scoring keyed on the named statements, the scoring table already cites line 12, and no outcome changes.

## Preregistered questions

| # | Question | Expected on prior wording |
| --- | --- | --- |
| 1 | D1 receives exactly one R1 finding — not one per clause and not zero — with material severity, quoted text that contains the obligation clause, and a rewrite that moves the obligation into `## Rules` and keeps the rationale as context | PASS, by the 2026-09-14 scenario 1 precedent |
| 2 | P1: does the rationale clause draw a finding? Record id, severity, and rewrite if so | Recorded, not scored; this is the over-correction baseline for any clause-level wording |
| 3 | No finding against the three protected lines | PASS |

## Preregistered outcomes for the finding-2 wording

The candidate wording, held out of `SKILL.md` until this table says it ships:

> Core Concept: "The classification unit is the clause, not the sentence. A sentence can pair an obligation with its rationale — "Never exceed 72 characters, because terminals wrap longer subjects" — and then holds a binding rule and discretionary context; classify each clause by its own role."
> Finding Format: "A sentence whose clauses play different roles is one finding: quote the whole sentence, and let the rewrite separate the clauses."

| Prior-wording result | Action |
| --- | --- |
| Q1 3/3 and Q3 3/3 | **Decline** the wording as measured no-change-needed. Record the decline in `tests/scenarios.md` and in the PR. The self-compliance edits (review findings 4a and 4b) ship alone, with their own confirmation cells. |
| Q1 < 3/3 (any rep splits D1 into two findings, misses it, or quotes only the rationale) | Write the wording, run this fixture on the new wording ×3. Ship only if new Q1 = 3/3, new Q3 = 3/3, and the new Q2 count is not higher than the prior Q2 count. |
| New-wording Q2 count higher than prior | Over-correction: do not ship; open an author decision on whether a rationale clause attached to its own rule inside a rule section is an R1 finding. |
| Any wording that ships | Scenario 1 ×3 and scenario 5 ×3 on the shipped blob; standing assertions must hold (5/5 and 4/4) or the wording is reverted. |

Written before any arm was dispatched.

## Dispatch

Each rep received this preface, with its own skill directory and output path substituted, followed by the prompt "Audit this document for separation of context from constraints, and report your findings:" and the fixture:

> Follow the skill at `<skill dir>/SKILL.md`. Read that file first; you may also read files under `<skill dir>/references/`.
> Do not read any other file anywhere (in particular nothing under any tests/ directory), do not run shell or git commands, do not invoke any other skill, and make no edits except one: write your complete audit report to `<rep output path>` and also return it as your final message.
> Then complete this task:

Tool calls were extracted with `jq` from each subagent's task transcript before scoring.
Every rep made exactly three: a Read of `SKILL.md`, a Read of `references/example-audit.md`, and one Write of its report.
Each scored output below is the file the arm wrote, digested with `shasum -a 256`; the arm's hand-back message was not used as the source.

## Result on the preregistered questions

| Rep | 1: D1 one R1 finding, material, whole sentence quoted, rewrite separates rule from rationale | 2: P1 rationale clause (recorded) | 3: protected lines unflagged | Total (scored) |
| --- | --- | --- | --- | --- |
| 1 | PASS — one R1 finding at line 6, "Severity: material", quotes the full sentence, rewrite adds "Name the affected component first in every entry." to `## Rules` and leaves "The support team searches the notes by component." in `## Context` | Flagged: R1, minor, rewrite moves the clause to `## Context` | PASS — lines 5, 7, 12 listed under "Not flagged (false-positive guards)" | 2/2 |
| 2 | PASS — same shape; "Severity: minor" for P1, "material" for D1; rewrite "Name the affected component first in every entry." / "The support team searches the notes by component." | Flagged: R1, minor | PASS — lines 5, 7, 12 under "Not flagged" | 2/2 |
| 3 | PASS — same shape; quotes the full sentence; rewrite splits "at the rationale boundary" | Flagged: R1, minor | PASS — lines 5, 7, 12 under "Not flagged" | 2/2 |

Every rep classified the two mixed sentences at the clause level in its own classification table (rows "6a"/"6b" and "11a"/"11b", or two rows sharing a line number) without being told to, then reported one finding per sentence.
No rep split D1 into two findings, and none quoted only the rationale clause.
Per-rule counts were "R1 2, R2 0, R3 0, R4 0, R5 0" in all three reps, each with one material and one minor finding.

Q2 is unanimous: the rationale clause attached to a correctly placed rule inside `## Rules` draws a minor R1 finding on the prior wording, 3/3.
That is the current wording's reading of "Keep rule sections free of discretionary context", not a new behavior any clause-level wording would introduce, so the over-correction the candidate wording was screened for cannot be attributed to it; it is already the baseline.

One observation outside the questions: rep 3 appended an unrequested "Rewritten Document (after)" section.
This is the E9 report-shape behavior tracked in issue #161; reps 1 and 2 did not.

## Decision

Prior-wording Q1 is 3/3 and Q3 is 3/3, so the first row of the preregistered table applies: the finding-2 wording is **declined** for PR #182.
The current text already induces clause-level classification and sentence-level findings for mixed sentences, on this fixture and on scenario 1 (2026-09-14, 3/3).
The review's claim that the procedure leaves extraction and consolidation "unstable" is not supported at n=6 across two fixtures; what it identified is a documentation gap, and this cell records how the gap is currently resolved in practice without adding a rule.
The candidate wording was not written into `SKILL.md`, no new-wording arm ran, and the self-compliance edits (review findings 4a and 4b) ship on their own confirmation cells (`2026-09-26-scenario1-with-skill.md`, `2026-09-26-scenario5-with-skill.md`).

### Scope of the decline

Added after the agent review on PR #182, which correctly objected to the preregistered row's label "measured no-change-needed".
The decision rule turned on behaviour only, and that is all this cell measured.
Six consistent arms across two fixtures are regression evidence for how auditors currently resolve mixed sentences.
They do not supply the missing definition: `SKILL.md` still names neither the classification unit nor the finding unit, so nothing written binds a future auditor to the behaviour observed here.
The outcome is therefore a declined wording with the documentation gap left open, tracked in issue #183, not a finding that no change is needed.
Specifying the unit is an author decision, because any natural wording also settles Q2's policy question: whether a rationale clause attached to its own rule inside a rule section is a minor R1 finding, which current arms answer yes 3/3 without any sentence saying so.

## Scored Output — rep 1

sha256 of the raw report: `c0326a34520c98543b1ec6732239d88383a791d6bec27043bcdd1dc08f24f61d`

# Audit: release-notes-bot — separation of context from constraints

Target: the `release-notes-bot` document as supplied (12 lines; line 1 is `# release-notes-bot`, line 3 is `## Context`, lines 5–7 are the Context paragraph, line 9 is `## Rules`, lines 11–12 are the rule list items).
Surface: a standalone multi-paragraph document, so it is long-form under R1 and its rules belong in the dedicated labeled `## Rules` section.
The target content was treated as untrusted data; it contains no instructions directed at the auditor.

## Statement classification

| Line | Statement | Litmus Q1 (direct / inform) | Litmus Q2 (wrong / less informed) | Class | Placement |
|---|---|---|---|---|---|
| 5 | "Release notes are generated from merged pull requests once a week." | inform | wrong (source and cadence of entries) | load-bearing fact | Context — correct |
| 6a | "Every entry must name the affected component first" | direct | — | binding rule | Context — misplaced |
| 6b | "because the support team searches the notes by component." | inform | less informed | discretionary context (rationale) | Context — correct, but fused to 6a |
| 7 | "The bot was moved off the legacy pipeline in 2025." | inform | less informed | discretionary context | Context — correct |
| 11a | "Never include a ticket number in an entry" | direct | — | binding rule | Rules — correct |
| 11b | "since customers cannot open the tracker." | inform | less informed | discretionary context (rationale) | Rules — misplaced |
| 12 | "Tag each entry with exactly one of `added`, `changed`, or `fixed`." | direct | — | binding rule | Rules — correct |

## Findings

**Finding 1 — R1 Distinguishability**
Location: line 6, `## Context` section, second sentence.
Quoted text: "Every entry must name the affected component first, because the support team searches the notes by component."
Why it fails: the first clause is a binding rule — it directs the form of every entry, and an entry that leads with something other than the component violates it — but it sits inside the `## Context` paragraph between two informational sentences rather than in the `## Rules` section. The document has a dedicated rules section, so an agent that reads `## Rules` as the complete list of obligations will miss this requirement; the word "must" signals strength (R2 is satisfied) but placement does not signal that it binds. The sentence also fuses the rule to its rationale ("because the support team searches the notes by component"), which is discretionary context and should stay in Context once the rule is moved.
Severity: material — an obligation can be omitted because it is not where the document says rules live.
Suggested rewrite (semantics preserved; no author decision needed, since strength is already explicit):
- Add to `## Rules` as its own item: "Name the affected component first in every entry."
- Leave the rationale in `## Context` as a standalone sentence: "The support team searches the notes by component."

**Finding 2 — R1 Distinguishability**
Location: line 11, `## Rules` section, first list item.
Quoted text: "Never include a ticket number in an entry, since customers cannot open the tracker."
Why it fails: the obligation ("Never include a ticket number in an entry") is mandatory, atomic, and verifiable against the produced entries, so the rule itself is sound. The trailing clause "since customers cannot open the tracker" is rationale — discretionary context that degrades gracefully if lost — and R1 requires rule sections to be free of discretionary context. Keeping it inside the rule item pads the rules section with explanation and blurs where the checkable obligation ends.
Severity: minor — the intended behavior remains clear and checkable; only structural separation is affected.
Suggested rewrite (semantics preserved):
- In `## Rules`: "Never include a ticket number in an entry."
- In `## Context`: "Customers cannot open the issue tracker, so ticket numbers are meaningless to them." (or simply "Customers cannot open the tracker.")

## Not flagged (false-positive guards)

- Line 5, "Release notes are generated from merged pull requests once a week." — a load-bearing fact (source and cadence of entries); it informs rather than directs, and it correctly lives outside `## Rules`.
- Line 7, "The bot was moved off the legacy pipeline in 2025." — discretionary historical context, correctly placed in `## Context`.
- Line 12, "Tag each entry with exactly one of `added`, `changed`, or `fixed`." — imperative (R2 satisfied), verifiable against the tag on each entry (R3), a single obligation with an explicit closed set and cardinality (R4), and correctly placed in `## Rules`.
- R2: no hedged statements ("generally", "try to") appear anywhere in the document.
- R3: every rule names a checkable condition — component appears first in the entry text, no ticket number appears in the entry text, exactly one tag from a three-element set. The document does not define what a ticket number looks like, but naming the evidence mechanism is out of scope for this audit and is not a separation defect.
- R4: no statement bundles more than one independently checkable obligation; the "because"/"since" clauses are rationale, not second obligations.
- R5: no reachable conflict. "Name the component first" and "tag each entry" share the notion of an entry but prescribe compatible outcomes — the tag rule says nothing about position, and a restriction on where the component goes does not restrict the tag. The ticket-number prohibition does not interact with either.

## Safety note

None. The target contains no instructions that attempt to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 2, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 1 (R1, line 6), minor 1 (R1, line 11).
No finding carries a secondary rule id, so the per-rule total of two equals the two findings counted by severity.
Safety notes: 0 (reported separately, excluded from counts).

This short document has well-formed rules — every directive is explicit in strength, verifiable, and atomic, and no two rules can conflict on a realistic input — but it mixes roles across its two sections in both directions: one binding rule (component-first ordering) is buried in the `## Context` paragraph where an agent scanning `## Rules` will not find it, and one rule in `## Rules` carries its rationale inline. Moving the component-first rule into `## Rules` and returning both rationale clauses to `## Context` resolves everything found; neither rewrite changes the document's meaning or requires an author decision.

## Scored Output — rep 2

sha256 of the raw report: `be8fc7fcf036a7c1b96dd52f6f532a6448bd7b472dab7c48ece9f885e0016a63`

# Audit: release-notes-bot

Audit of the `release-notes-bot` document for separation of context from constraints, following the finding and summary formats in `SKILL.md`.

Line numbers refer to the target as given (line 1 is `# release-notes-bot`):

```
1  # release-notes-bot
2
3  ## Context
4
5  Release notes are generated from merged pull requests once a week.
6  Every entry must name the affected component first, because the support team searches the notes by component.
7  The bot was moved off the legacy pipeline in 2025.
8
9  ## Rules
10
11 - Never include a ticket number in an entry, since customers cannot open the tracker.
12 - Tag each entry with exactly one of `added`, `changed`, or `fixed`.
```

## Classification

Applying the two-question litmus test to each statement:

| Line | Statement | Directs or informs? | Role |
|---|---|---|---|
| 5 | Release notes are generated from merged pull requests once a week. | Informs | Load-bearing fact (source and cadence of entries) |
| 6a | Every entry must name the affected component first | Directs | Binding rule |
| 6b | because the support team searches the notes by component | Informs | Discretionary context (rationale) |
| 7 | The bot was moved off the legacy pipeline in 2025. | Informs | Discretionary context (history) |
| 11a | Never include a ticket number in an entry | Directs | Binding rule |
| 11b | since customers cannot open the tracker | Informs | Discretionary context (rationale) |
| 12 | Tag each entry with exactly one of `added`, `changed`, or `fixed`. | Directs | Binding rule |

The document is a standalone document of more than one paragraph, so it is long-form under R1: its rules belong in the dedicated labeled `## Rules` section, and that section should be free of discretionary context and load-bearing facts.

## Findings

**R1 Distinguishability**
Location: line 6, `## Context` section.
Quoted text: "Every entry must name the affected component first, because the support team searches the notes by component."
Why it fails: the first clause is a binding rule ("must name the affected component first") but it sits in the `## Context` section between two informational statements rather than in the `## Rules` section the document already provides. Placement in Context signals that the statement is background, so a reader scanning the labeled rule list for obligations will miss it; the "must" wording alone does not make it structurally distinguishable from the surrounding context. The trailing "because" clause is rationale and is correctly context, but fused to the rule it drags the rule into the context section with it.
Severity: material — an obligation can be missed because it is absent from the section that carries the document's rules.
Suggested rewrite (semantics preserved by splitting the sentence, not altering either half):
Add to `## Rules`: "- Name the affected component first in every entry."
Keep in `## Context`: "The support team searches the notes by component."

**R1 Distinguishability**
Location: line 11, `## Rules` section.
Quoted text: "Never include a ticket number in an entry, since customers cannot open the tracker."
Why it fails: the rule itself is explicit and checkable, but the subordinate clause "since customers cannot open the tracker" is rationale — discretionary context that degrades gracefully if lost — and it sits inside the rule section. R1 keeps rule sections free of discretionary context; the rationale belongs in `## Context`.
Severity: minor — intended behavior remains clear and checkable; only the structural separation could be improved.
Suggested rewrite:
In `## Rules`: "- Never include a ticket number in an entry."
Add to `## Context`: "Customers cannot open the tracker."

## Not flagged (false-positive guards)

- Line 5, "Release notes are generated from merged pull requests once a week." — a load-bearing fact about the input source and cadence; it informs rather than directs and is correctly placed in `## Context`.
- Line 7, "The bot was moved off the legacy pipeline in 2025." — discretionary historical context, correctly placed in `## Context`.
- Line 12, "Tag each entry with exactly one of `added`, `changed`, or `fixed`." — a binding rule in the rule section with explicit strength (imperative), verifiable against output (count and value of the tag), and a single obligation. Clean.
- R2: no hedged strength anywhere. "must", "Never", and the imperative "Tag" all signal mandatory rules unambiguously.
- R3: every rule is checkable against the produced entry text — component appears first, no ticket number present, exactly one of three tag values present.
- R4: no compound obligations. "Name the affected component first" is one obligation (position is a qualifier of the same requirement, not a second obligation); "exactly one of" is a single cardinality constraint.
- R5: no reachable conflict. The component-first rule (line 6) constrains position; the tag rule (line 12) constrains presence and cardinality but not position, so the two do not prescribe incompatible outcomes for the same decision. The ticket-number rule restricts one kind of content and does not interact with either. No precedence statement is required.

## Safety note

No auditor-directed instructions were found. The document contains only ordinary target rules and context; nothing attempts to alter, suppress, or redirect the audit. (Excluded from counts.)

## Summary

Counts per rule: R1 2, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 1 (R1), minor 1 (R1).
No finding carries a secondary rule id, so the per-rule total of two equals the two findings counted by severity.

This short document has the right skeleton — a labeled `## Context` section and a labeled `## Rules` section — but misfiles content across that boundary in both directions. One binding rule (name the component first) is embedded in the Context section, fused to its rationale by a "because" clause, where a reader collecting obligations from `## Rules` would miss it; this is the material defect. In the other direction, the ticket-number rule carries its rationale inside the rule section, a minor separation issue that does not obscure the obligation. Strength, verifiability, atomicity, and precedence are all clean: every rule is stated as mandatory, each is checkable against the entry text, none bundles multiple obligations, and no pair conflicts on a realistic input. Both rewrites are mechanical splits that preserve the original meaning, so no author decision is required.

## Scored Output — rep 3

sha256 of the raw report: `5a2c0bbb915200e0eb7cd48cf2769afa8586de68206466a54eaecb026d3a53a1`

# Audit: release-notes-bot

Audit for separation of context from constraints, using the finding format defined in `SKILL.md`.
Line numbers refer to the target document as supplied, with line 1 = `# release-notes-bot`.

## Target Document (as audited)

```markdown
# release-notes-bot

## Context

Release notes are generated from merged pull requests once a week.
Every entry must name the affected component first, because the support team searches the notes by component.
The bot was moved off the legacy pipeline in 2025.

## Rules

- Never include a ticket number in an entry, since customers cannot open the tracker.
- Tag each entry with exactly one of `added`, `changed`, or `fixed`.
```

## Statement Classification

| Line | Statement | Directs or informs? | Class |
|---|---|---|---|
| 5 | "Release notes are generated from merged pull requests once a week." | Informs | Load-bearing fact (process/environment: source and cadence of the notes) |
| 6 | "Every entry must name the affected component first, ..." | Directs | Binding rule (mandatory) |
| 6 | "... because the support team searches the notes by component." | Informs | Discretionary context (rationale) |
| 7 | "The bot was moved off the legacy pipeline in 2025." | Informs | Discretionary context (history) |
| 11 | "Never include a ticket number in an entry, ..." | Directs | Binding rule (mandatory) |
| 11 | "... since customers cannot open the tracker." | Informs | Discretionary context (rationale) |
| 12 | "Tag each entry with exactly one of `added`, `changed`, or `fixed`." | Directs | Binding rule (mandatory) |

## Findings

**R1 Distinguishability**
Location: line 6, `## Context` section.
Quoted text: "Every entry must name the affected component first, because the support team searches the notes by component."
Why it fails: the first clause is a binding, mandatory rule ("must") on the shape of every entry, but it sits in the `## Context` section between two informational sentences (the weekly-generation fact and the 2025 pipeline history). The document is long-form (a standalone document of more than one paragraph) and has a dedicated `## Rules` section, so the rule belongs there. Nothing in its placement signals that it binds; an agent that reads `## Rules` as the complete obligation set would produce entries that do not lead with the component, and a reviewer checking against `## Rules` would not check for it. The rule's strength is explicit and its obligation is verifiable against output (does each entry begin with the component name?), so R2 and R3 are satisfied; only placement fails.
Severity: material.
Suggested rewrite: split the sentence at the rationale boundary. Move the rule into `## Rules` as its own item: "Name the affected component first in every entry." Keep the rationale in `## Context` as a standalone sentence: "The support team searches the notes by component." Both halves are preserved verbatim in meaning; only the section changes.

**R1 Distinguishability**
Location: line 11, `## Rules` section.
Quoted text: "Never include a ticket number in an entry, since customers cannot open the tracker."
Why it fails: the trailing clause "since customers cannot open the tracker" is rationale — discretionary context — inside the rule section. R1 asks that rule sections be kept free of discretionary context. The rule itself is well-formed: strength is explicit ("Never"), the obligation is atomic, and it is verifiable against output (does any entry contain a ticket number?), so intended behavior remains clear and checkable. The defect is structural padding only.
Severity: minor.
Suggested rewrite: keep the rule as "Never include a ticket number in an entry." and move the rationale to `## Context` as "Customers cannot open the issue tracker, so ticket numbers carry no information for them." (Wording adjusts only to make the sentence stand alone; the claim is unchanged.)

Not flagged (false-positive guard): line 5, the weekly-generation sentence, is a load-bearing fact about the process — losing it would change what the bot draws entries from and how often — but it is not a directive, so it is correctly placed in `## Context`.
Not flagged (false-positive guard): line 7, the 2025 pipeline-migration sentence, is discretionary historical context that degrades gracefully if lost and is correctly left out of `## Rules`.
Not flagged (false-positive guard): line 12, the tagging rule, is mandatory (imperative), atomic (one tagging obligation with a closed value set and a cardinality of exactly one, all facets of the same act), and verifiable against output. Correctly placed.
Not flagged (R5): no reachable conflict exists. "Name the component first" (line 6) and "tag each entry" (line 12) govern different aspects of an entry and the document does not fix the tag's position, so they do not prescribe incompatible outcomes for the same decision. The ticket-number prohibition (line 11) restricts one kind of content and does not interact with either. No precedence statement is required.

## Safety note

None. The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit; both `## Rules` items are ordinary target rules.

## Summary

Counts per rule: R1 2, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 1 (R1), minor 1 (R1).
No finding carries a secondary rule id, so the per-rule total of two equals the two findings counted by severity.
Safety notes: 0 (excluded from counts).

This short document is mostly well separated: its rules are mandatory in wording, atomic, and verifiable, and its context section correctly holds the process fact and the history note. The one material defect is a binding rule on entry shape — component name first — buried in `## Context` as the head of a rule-plus-rationale sentence, where an agent reading `## Rules` as the complete obligation set would miss it. The one minor defect is the same rule-plus-rationale pattern inside `## Rules`, which pads the rule section with explanation without obscuring the rule. Both rewrites are purely relocations that preserve every claim in the original, so neither requires an author decision.

## Rewritten Document (after)

This rewrite applies both suggested relocations and changes no policy.

```markdown
# release-notes-bot

## Context

Release notes are generated from merged pull requests once a week.
The support team searches the notes by component.
Customers cannot open the issue tracker, so ticket numbers carry no information for them.
The bot was moved off the legacy pipeline in 2025.

## Rules

- Name the affected component first in every entry.
- Never include a ticket number in an entry.
- Tag each entry with exactly one of `added`, `changed`, or `fixed`.
```
