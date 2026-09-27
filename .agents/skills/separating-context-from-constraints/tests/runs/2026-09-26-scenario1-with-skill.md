# Scenario 1 — With-Skill Confirmation Cell (review 2026-09-26 self-compliance edits)

Date: 2026-09-26
Run: with-skill
SKILL.md blob: 2cf05a14742393e4e7138e9763d5b05b5008b344
Commit: none — run against the uncommitted working tree on branch `fix/context-constraints-review-20260926` (head `a732d56`, which holds only the preregistered mixed-sentence cell; the `SKILL.md` edits were uncommitted at dispatch and are committed with this artifact)
Referenced files: references/example-audit.md f825b78fff6df83c0218ac30f7c020a1c142942b
Model: claude-fable-5-1, the session model at dispatch, inherited by each subagent with no per-agent override
Harness: Claude Code 2.1.283, Agent tool, general-purpose subagent, three independent dispatches in one parallel batch of six (with the scenario 5 reps)
Prompt: the scenario prompt from `tests/scenarios.md`, verbatim, preceded by the preface quoted under "Dispatch" below
Sampling: harness default
Scorer: Claude Fable 5.1 (claude-fable-5-1), the session model, 2026-09-26, unblinded
Notes: Confirmation cell for two `SKILL.md` edits made in response to the 2026-09-26 review's findings 4a and 4b: the litmus-test imperative in Core Concept became a definition (the command already lives in Audit Procedure step 2), and the sentence "Defaults and defeasible guidance are legitimate rules, not failed constraints" moved from R2 into Core Concept's binding-rules role. Scenario 1 is the cell for the litmus-test change: its three buried rules are found only by classifying every statement, so a weakened classification step would show here first. Each subagent transcript also carried the harness's auto-mode tool-preference reminder once (checked by grep in all fifteen transcripts of this session); every arm nonetheless made only the three tool calls its preface permitted.

## Why this cell

The 2026-09-26 review found that `SKILL.md` did not follow its own R1 in two places.
Core Concept carried a procedural command ("Apply this two-question litmus test to each statement"), and R2 carried a classification definition ("Defaults and defeasible guidance are legitimate rules, not failed constraints").
Both are minor by the skill's own severity scale.
The fix removed the imperative from Core Concept, leaving the definition (Audit Procedure step 2 already says to classify each statement with the test), and moved the defaults sentence into the binding-rules role in Core Concept, with R2 keeping its own strength test.
Under the adopted protocol, an edit that removes a command from one home while its authoritative home stays owes a cell where that command does the work.
Scenario 1 is that cell for the litmus test: every one of its three defects is found by classification, and the 2026-09-14 reps on the prior wording (blob `713c696`) are the paired prior-wording arm at 5/5 ×3.

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
| 1 | The arm still classifies every body statement with the litmus test (a classification table or equivalent statement-by-statement pass appears) and reaches all three buried rules | PASS | Table "Litmus-test classification of the body's statements" with nine rows; "Three binding rules exist; none is placed in a labeled rules section" |
| 2 | Same | PASS | Table "Statement classification (litmus test)" with ten rows; three "**Binding rule** — buried" rows |
| 3 | Same | PASS | Table "Statement-by-statement litmus test on the body" with nine rows; "Three binding rules, zero of them structurally distinguishable from context." |

## Result on the scenario's standing assertions

| Rep | 1: conventional-commit clause, R1 | 2: 72-character clause, R1 | 3: test-plan clause, R1 | 4: all three material | 5: no finding against background sentences | Total |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | PASS | PASS | PASS | PASS ("material 3, minor 0") | PASS | 5/5 |
| 2 | PASS | PASS | PASS | PASS ("material 3, minor 0") | PASS | 5/5 |
| 3 | PASS | PASS | PASS | PASS ("material 3, minor 0") | PASS | 5/5 |

Each rep's three R1 findings quote the clause, locate it by line, and rewrite it into a new `## Rules` section; per-rule counts are "R1 3, R2 0, R3 0, R4 0, R5 0" in all three.
Each rep lists the "People joke" and `CHANGELOG.md` sentences under its not-flagged guards.

Observations outside the assertions, recorded for issue #161 (E9) and the wave-3 report-shape work:

- Reps 1 and 2 appended an unrequested full rewritten document; rep 3 did not. Rep 2's rewrite rewords the protected "People joke" sentence; rep 1's keeps it verbatim. The 2026-09-14 cell had 3/3 rewrites; this cell has 2/3.
- Reps 1 and 2 marked the test-plan rule's scope (every commit or the pull request's commits) as an author decision with two labeled readings; rep 3 recorded the same question as a note for the author without labeling it an author decision. The 2026-09-14 cell had this at 1/3.

Neither observation is attributed to the edits: the prior-wording cell shows both behaviors, and the differences are within what three reps can show.

## Scored Output — rep 1

sha256 of the raw report: `cabb7a88f20ead7e2c44fb909c6ba25527e67d22c064e7de2cb322b64a5dee70`

# Audit: `commit-message-helper` — separation of context from constraints

Line numbers below count the document's first line (the opening `---` of the frontmatter) as line 1.

## Surfaces and classification

The target carries two instruction-bearing surfaces, classified separately per R1:

- **Frontmatter `description` (line 3)** — compact surface. Its single statement, "Use when drafting commit messages for this repo.", is a trigger rule marked inline with an imperative sentence. Clean.
- **Body (lines 6–22)** — a standalone document of more than one paragraph, so long-form. It has no dedicated rules section; its headings are `## Background` and `## Notes`.

Litmus-test classification of the body's statements:

| Line | Statement (abbreviated) | Class |
|---|---|---|
| 8 | history has drifted across tools | discretionary context |
| 9 | "we agreed messages should always start with a lowercase conventional-commit type…" | **binding rule** (wrapped in narrative) |
| 10 | team has been happy since adoption | discretionary context |
| 14 | release-notes generator extracts the type prefix to build the changelog | load-bearing fact (tool semantics / rationale for line 9) |
| 15 | consistent messages make automated changelog generation possible | discretionary context (rationale) |
| 16 | "the subject line must never exceed 72 characters…" | **binding rule** (wrapped in "It's also worth noting" + rationale) |
| 17 | people joke everybody breaks this rule | discretionary context |
| 21 | "the commit body must include a 'Test plan' section…" | **binding rule** (wrapped in "By the way" + rationale) |
| 22 | generator reads `CHANGELOG.md` at repo root | load-bearing fact (tool semantics) |

Three binding rules exist; none is placed in a labeled rules section, and all three are stated mid-paragraph inside sections whose headings (`Background`, `Notes`) signal non-binding content.

## Findings

**R1 Distinguishability**
Location: line 9.
Quoted text: "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
Why it fails: this is the document's primary formatting rule (and, per line 14, the one the release-notes generator depends on), but it is delivered as a historical anecdote — "when we finally settled… we agreed…" — sandwiched between two sentences of pure history (lines 8 and 10) in the untitled intro paragraph. Nothing structural marks it as a directive; an agent reading the intro as backstory can miss it entirely. The strength itself ("should always") reads as mandatory, reinforced by the generator dependence in line 14, so no R2 id is attached. The obligation is checkable against the drafted message (R3 satisfied).
Severity: material.
Suggested rewrite: add a `## Rules` section and state the rule there as its own item: "Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`)." Keep the history as context, e.g. in `## Background`: "The convention was settled during the 2023 tooling cleanup, and the team has been happy with it since."

**R1 Distinguishability**
Location: line 16.
Quoted text: "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
Why it fails: a mandatory, precisely checkable limit ("must never exceed 72 characters") is placed in `## Background` — a section whose heading signals non-binding content — and is introduced with the discounting lead-in "It's also worth noting", then fused with its rationale in the same sentence. The following sentence (line 17, "the one rule everybody breaks eventually") further colors it as negotiable flavor rather than a requirement. Strength is explicit (R2 satisfied) and the rule is verifiable by counting characters in the drafted subject line (R3 satisfied); the defect is purely placement and framing.
Severity: material.
Suggested rewrite: in `## Rules`: "Keep the subject line at 72 characters or fewer." Retain the rationale in `## Background`: "Several terminal-based git tools truncate or wrap subject lines longer than 72 characters during review." Line 17 may stay as context; once the rule is in the rules section it no longer competes with it.

**R1 Distinguishability**
Location: line 21.
Quoted text: "By the way, before you open a pull request the commit body must include a \"Test plan\" section describing how the change was verified — reviewers have flagged its absence in the past."
Why it fails: a mandatory content requirement for the commit body is placed in `## Notes`, opened with "By the way", and fused with its rationale ("reviewers have flagged its absence"). An agent drafting a commit message that skims the document for requirements finds no rules section and is likely to treat this as an aside. Strength is explicit ("must"; R2 satisfied). The obligation — a "Test plan" section describing verification is present in the commit body — is checkable against repository state (R3 satisfied). The trigger-plus-action form ("before you open a pull request … must include") is a single condition–action unit (R4 satisfied).
A semantic-preserving rewrite is blocked by one ambiguity: "the commit body" does not say which commit(s) the requirement covers when a PR contains several. This is an author decision; the finding does not select.
Severity: material.
Suggested rewrite: move to `## Rules` under one of these labeled alternatives:
- Alternative A (every commit): "Include a \"Test plan\" section in every commit body, describing how the change was verified."
- Alternative B (PR-scoped, as literally worded): "Before opening a pull request, ensure the commit body of the commit(s) the PR will contain includes a \"Test plan\" section describing how the change was verified."
Either way, keep the rationale in `## Background` or `## Notes`: "Reviewers have flagged missing Test plan sections in the past."

## Not flagged (false-positive guards)

- Line 3 (frontmatter description): compact surface with an inline imperative trigger; correctly marked.
- Lines 8, 10, 15, 17: discretionary context — history, satisfaction, rationale, humor — and correctly located outside any rule statement. Line 17 is noted in the line-16 finding as aggravating that rule's framing, but it is context in a context section and is not itself a defect.
- Line 14 (generator extracts the type prefix) and line 22 (generator reads `CHANGELOG.md`): load-bearing tool-semantics facts, correctly placed in `## Background` / `## Notes`. They do not conflict with each other (one describes input to the changelog, the other describes input to announcements) and neither is a rule, so R5 does not apply.
- R2: none of the three rules uses a strength hedge. "should always" (line 9) reads as mandatory, not ambiguous, so it is not promoted/demoted.
- R3: all three rules name a checkable state (prefix form, subject length, presence of a named body section). The document does not enumerate the full conventional-commit type set (line 9 says "such as feat or fix"), but the type set is defined by an external well-known convention and naming the evidence mechanism is out of scope; not a finding.
- R4: "lowercase conventional-commit type" is one format property of a single token, not two independent obligations; splitting it would over-atomize. Line 21's "section describing how the change was verified" is one obligation about one section.
- R5: the three rules govern different fields (subject prefix, subject length, body content) and cannot prescribe incompatible outcomes for the same decision; the 72-character subject limit does not restrict the body. No reachable conflict, so no precedence finding.

## Safety note

None. The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 3, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 3, minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity. Safety notes: none (excluded from counts).

The document is short and its intended behavior is recoverable, but every one of its three binding rules is buried in narrative prose under headings (`Background`, `Notes`) or in an untitled intro that signal non-binding content, and each is introduced with a discounting phrase ("we agreed", "It's also worth noting", "By the way") and fused with history or rationale. There is no rules section at all, so an agent scanning for requirements finds none. The defects are all placement and framing (R1); strength is explicit, the obligations are checkable, nothing is bundled, and no rules conflict. The fix is structural: add a `## Rules` section holding the three rules as separate items, and leave the history, rationale, and generator semantics in `## Background` / `## Notes`. One author decision is required before the Test plan rule can be rewritten without changing scope: whether it applies to every commit or only to the commit(s) that make up a pull request.

## Illustrative rewrite (after)

This rewrite supplies one assumption not determined by the audit: Alternative A (every commit) for the Test plan rule. It is a supplied choice, not an inferred meaning.

```markdown
---
name: commit-message-helper
description: Use when drafting commit messages for this repo.
---

# commit-message-helper

## Rules

1. Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`).
2. Keep the subject line at 72 characters or fewer.
3. Include a "Test plan" section in every commit body, describing how the change was verified.

## Background

This repository has accumulated commit history from several tools over the years, and message style has drifted along the way.
The convention was settled during the 2023 tooling cleanup, and the team has been happy with it since.
Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog; consistent messages make automated changelog generation possible.
Several terminal-based git tools truncate or wrap subject lines longer than 72 characters during review. People joke that this is the one rule everybody breaks eventually.
Reviewers have flagged missing Test plan sections in the past.

## Notes

The release-notes generator reads the `CHANGELOG.md` file at the repo root to produce release announcements.
```

## Scored Output — rep 2

sha256 of the raw report: `37b6e7fade372dd669473b51e6dc1913c65911aaf257b9d852ea4cd7e3906191`

# Audit: `commit-message-helper` — separation of context from constraints

Line numbers count from the opening `---` of the frontmatter as line 1 (blank lines included).

## Surface classification

- **Frontmatter `description`** (line 3) — compact surface. "Use when drafting commit messages for this repo." is a single imperative trigger sentence; its one directive is marked inline. No finding.
- **Body** (lines 6–22) — standalone document of more than one paragraph, so long-form. It has `## Background` and `## Notes` sections but **no dedicated labeled rule section**. Every binding rule in the body is embedded in narrative prose. The three findings below are all instances of this one structural gap; per the consolidation rule they are reported one per misplaced statement.

## Statement classification (litmus test)

| Line | Statement (abbreviated) | Role |
|---|---|---|
| 3 | "Use when drafting commit messages for this repo." | Binding rule (trigger), inline-marked — OK |
| 8 | history has drifted across several tools | Discretionary context |
| 9 | "we agreed messages should always start with a lowercase conventional-commit type such as feat or fix" | **Binding rule** — buried |
| 10 | team has been happy since adoption | Discretionary context |
| 14 | release-notes generator extracts the type prefix to build the changelog | Load-bearing fact (tool semantics) |
| 15 | contributors ask why; consistency enables changelog generation | Discretionary context (rationale) |
| 16 | "the subject line must never exceed 72 characters, since ..." | **Binding rule** — buried, plus rationale |
| 17 | "People joke that this is the one rule everybody breaks eventually." | Discretionary context |
| 21 | "before you open a pull request the commit body must include a 'Test plan' section ... — reviewers have flagged its absence" | **Binding rule** — buried, plus rationale |
| 22 | generator reads `CHANGELOG.md` at repo root to produce release announcements | Load-bearing fact (tool semantics) |

## Findings

### Finding 1 — R1 Distinguishability

- **Location:** line 9, opening paragraph (under the `# commit-message-helper` heading, before `## Background`).
- **Quoted text:** "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
- **Why it fails:** This is the document's central binding rule (it is what the release-notes generator depends on, per line 14), but it is delivered as reported speech inside a historical anecdote — "when we settled ... we agreed ..." — sandwiched between two sentences of pure flavor (lines 8 and 10). Nothing structural marks it as a directive to the agent rather than a description of what the team once decided. In a long-form document R1 requires binding rules to sit in a dedicated labeled section; this document has none. The rule's own strength wording ("should always") is not hedged enough to trigger R2, so this is an R1 defect only.
- **Severity:** Material — an agent skimming for instructions can read the whole opening paragraph as background and miss the obligation.
- **Suggested rewrite:** Add a `## Rules` section and place the rule there as its own item, stated directly to the reader:
  > Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`).

  Move the history to a context section, unchanged in meaning:
  > The convention was settled during the 2023 tooling cleanup after message style drifted across several tools.

  Note for the author (not a semantic change, so not part of the rewrite): the original specifies only that the message *starts with* a lowercase type; it does not specify the separator or scope syntax (`type:` / `type(scope):`). If a full subject format is intended, that is an addition the author must make explicitly.

### Finding 2 — R1 Distinguishability

- **Location:** line 16, `## Background` section.
- **Quoted text:** "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
- **Why it fails:** A mandatory rule ("must never exceed 72 characters") is introduced with the aside marker "It's also worth noting", placed third in a paragraph of rationale about the changelog generator, and fused in one sentence with its justification ("since several terminal-based git tools ..."). Its placement in a section titled `Background` signals context, not constraint. The immediately following sentence (line 17, "People joke that this is the one rule everybody breaks eventually.") is discretionary flavor that, sitting directly after the rule, invites a reader to treat it as negotiable; that sentence is not itself a finding (it is not a rule and there is no rule section for it to pollute), but the rewrite separates it from the rule. The rule's own wording is unambiguously mandatory, so R2 is not cited.
- **Severity:** Material — the rule can be missed, and its "Background" placement plus the adjacent joke could plausibly lead an agent to exceed the limit.
- **Suggested rewrite:** In the `## Rules` section:
  > Keep the commit subject line at 72 characters or fewer.

  Move the rationale to the context section:
  > Several terminal-based git tools truncate or wrap subject lines longer than 72 characters during review.

  The line 17 joke may be kept in the context section or dropped; either way it must not sit inside or adjacent to the rule.

### Finding 3 — R1 Distinguishability

- **Location:** line 21, `## Notes` section.
- **Quoted text:** "By the way, before you open a pull request the commit body must include a "Test plan" section describing how the change was verified — reviewers have flagged its absence in the past."
- **Why it fails:** A mandatory obligation ("must include a 'Test plan' section") is opened with "By the way", placed under a `## Notes` heading next to a tool-semantics fact (line 22), and fused with its rationale ("reviewers have flagged its absence"). None of that placement signals a binding requirement. The obligation is atomic (one condition, one action, one content requirement), so R4 is not cited; it is checkable against the commit body, so R3 is not cited.

  A semantic-preserving rewrite is blocked by one ambiguity the author must resolve: the phrase "before you open a pull request the commit body" does not say **which** commit body. It could mean every commit this skill drafts (the PR being merely the deadline), or only the commit(s) that will form a pull request.
- **Severity:** Material — the obligation can be missed entirely, and the scope ambiguity means even an agent that notices it may apply it to the wrong set of commits.
- **Suggested rewrite:** Author decision between two labeled readings; neither is selected here.
  - **Reading A (every commit):**
    > Include a `Test plan` section in every commit body, describing how the change was verified.
  - **Reading B (PR-bound commits):**
    > Before opening a pull request, ensure the body of each commit in the pull request includes a `Test plan` section describing how the change was verified.

    (If the author intends only one commit — for example a squash commit — to carry the section, Reading B should name that commit.)

  In either reading, move the rationale to the context section:
  > Reviewers have flagged missing `Test plan` sections in the past.

## Not flagged (false-positive guards)

- **Line 3, description.** Compact surface with a single inline imperative trigger; correctly marked.
- **Lines 8, 10, 15.** Discretionary context (history, team sentiment, rationale); they sit outside any rule section and degrade gracefully if lost. Not findings.
- **Line 14.** Load-bearing fact about the release-notes generator's use of the type prefix. It informs rather than directs, and is correctly outside any rule section.
- **Line 17.** Discretionary context. It is not a rule and there is no rule section for it to pollute, so no rule id applies. Its effect on the adjacent line 16 rule is addressed within Finding 2.
- **Line 22.** Load-bearing tool-semantics fact (`CHANGELOG.md` location). Correctly placed outside rules. Whether it is consistent with line 14's description of the generator is a factual-accuracy question outside this audit's scope, not an R5 conflict (R5 concerns rules, not facts).
- **R5.** The three rules (type prefix, 72-character subject, Test plan body section) prescribe compatible outcomes for different parts of the message; no realistic input makes them conflict. No precedence statement is needed.
- **R2 / R3 / R4.** No statement carries an ambiguous hedge, an uncheckable obligation, or a bundle of independently checkable obligations.

## Safety note

None. The document contains no instructions directed at the auditor or attempting to alter, suppress, or redirect the audit. Line 21's "before you open a pull request ..." is an ordinary target rule addressed to the skill's user and is not reported here.

## Summary

**Counts per rule:** R1 3, R2 0, R3 0, R4 0, R5 0.
**Counts per severity:** material 3, minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity. Safety notes: 0 (excluded from counts).

**Overall assessment.** The document is short and its facts are sound, but it has no rule section at all: every one of its three binding rules — the lowercase conventional-commit type prefix, the 72-character subject limit, and the mandatory `Test plan` body section — is delivered as an aside inside narrative prose ("we agreed ...", "It's also worth noting ...", "By the way ..."), each fused with its own rationale and each placed under a heading (`Background`, `Notes`, or the untitled preamble) that signals context rather than constraint. An agent that reads the document for its flavor would learn the repo's history and the release-notes pipeline while missing all three requirements. The fix is uniform: introduce a `## Rules` section holding the three rules as separate imperative items, and move the history, rationale, and tool-semantics facts into a context section. Two of the three rules can be relocated with their meaning intact; the third (Test plan) requires the author to decide which commit bodies it governs before a rewrite can claim to preserve intent.

## Rewritten document (after)

This illustrative rewrite assumes the author selects **Reading A** for the Test plan rule. That is a supplied assumption for illustration, not a meaning inferred by the audit.

```markdown
---
name: commit-message-helper
description: Use when drafting commit messages for this repo.
---

# commit-message-helper

## Rules

1. Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`).
2. Keep the commit subject line at 72 characters or fewer.
3. Include a `Test plan` section in every commit body, describing how the change was verified.

## Context

This repository has accumulated commit history from several tools over the years, and message style drifted along the way.
The convention was settled during the 2023 tooling cleanup, and the team has been happy with it since adoption.
Contributors sometimes ask why formatting matters; consistent messages are what make automated changelog generation possible.
Several terminal-based git tools truncate or wrap subject lines longer than 72 characters during review.
People joke that the subject-length limit is the one rule everybody breaks eventually.
Reviewers have flagged missing `Test plan` sections in the past.

## Tool semantics

The release-notes generator extracts the conventional-commit type prefix from commit messages to build the changelog.
It reads the `CHANGELOG.md` file at the repo root to produce release announcements.
```

## Scored Output — rep 3

sha256 of the raw report: `1281122b55f8610245a3a2e5112d93f503ff0b368d642a6a7e04f3487cc60942`

# Audit: `commit-message-helper` — separation of context from constraints

Line numbers refer to the target document as supplied, counting the opening `---` of the frontmatter as line 1.

## Surfaces and classification

The target carries two instruction-bearing surfaces, classified separately per R1:

- **Frontmatter `description` (line 3)** — compact surface. It contains a single trigger statement ("Use when drafting commit messages for this repo.") and no binding rules. Nothing to mark inline; no finding.
- **Body (lines 6–22)** — a standalone document of more than one paragraph, so long-form. Long-form surfaces must carry their rules in a dedicated labeled section. The body has no such section: its headings are `## Background` and `## Notes`, and every binding rule sits inside a narrative paragraph under one of those headings or in the unlabeled intro.

Statement-by-statement litmus test on the body:

| Line | Statement (abridged) | Directs or informs? | If lost? | Class |
|---|---|---|---|---|
| 8 | commit history accumulated from several tools; style drifted | informs | less informed | discretionary context |
| 9 | "we agreed messages should always start with a lowercase conventional-commit type such as feat or fix" | directs | wrong output | **binding rule** (buried) |
| 10 | team has been happy since adoption | informs | less informed | discretionary context |
| 14 | release-notes generator extracts the type prefix to build the changelog | informs | wrong (explains what the prefix feeds) | load-bearing fact |
| 15 | contributors ask why; consistency enables changelog automation | informs | less informed | discretionary context |
| 16 | "the subject line must never exceed 72 characters" | directs | wrong output | **binding rule** (buried) |
| 17 | people joke this is the rule everyone breaks | informs | less informed | discretionary context |
| 21 | "before you open a pull request the commit body must include a 'Test plan' section describing how the change was verified" | directs | omitted obligation | **binding rule** (buried) |
| 22 | generator reads `CHANGELOG.md` at repo root for release announcements | informs | less informed for this task | discretionary context / tool semantics |

Three binding rules, zero of them structurally distinguishable from context.

## Findings

### Finding 1 — R1 Distinguishability

- **Location:** line 9 (unlabeled intro paragraph).
- **Quoted text:** "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
- **Why it fails:** This is the document's central rule — the type prefix is what the release-notes generator keys on (line 14) — but it is delivered as reported speech inside a history paragraph ("When we finally settled... we agreed..."). Nothing in its placement or framing signals that it binds the agent now; it reads as an account of a past team decision, sandwiched between two sentences of pure background (lines 8 and 10). An agent skimming for requirements can follow the flavor ("style has drifted", "the team has been happy") and miss the obligation. The strength signal itself ("always") is explicit, so this is not an R2 finding; the defect is placement and narrative framing.
- **Severity:** material.
- **Suggested rewrite:** Create a `## Rules` section and move the obligation there as its own item, keeping the historical framing in context:
  - Rule: "Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`)."
  - Context (leave in the intro paragraph or a `## Background` section): "The convention was settled during the 2023 tooling cleanup."

### Finding 2 — R1 Distinguishability

- **Location:** line 16 (`## Background`).
- **Quoted text:** "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
- **Why it fails:** A mandatory, verifiable rule ("must never exceed 72 characters") is introduced with "It's also worth noting that" — phrasing that marks an aside — and placed in a section titled `## Background`, whose heading tells the reader its contents are informative rather than directive. The rationale clause ("since several terminal-based git tools...") is fused into the same sentence, and the following sentence (line 17, "the one rule everybody breaks eventually") is flavor that further invites the reader to treat the limit as negotiable. The rule's own strength wording is explicit, so R2 does not apply; the problem is that the section label, the aside framing, and the surrounding commentary all signal "context" for a statement that binds.
- **Severity:** material.
- **Suggested rewrite:** Move the obligation into the `## Rules` section as its own item and leave the rationale behind:
  - Rule: "Keep the subject line at 72 characters or fewer."
  - Context (stays in `## Background`): "Several terminal-based git tools truncate or wrap subject lines longer than 72 characters during review." Line 17 may stay as discretionary context or be dropped; it carries no obligation either way.

### Finding 3 — R1 Distinguishability

- **Location:** line 21 (`## Notes`).
- **Quoted text:** "By the way, before you open a pull request the commit body must include a \"Test plan\" section describing how the change was verified — reviewers have flagged its absence in the past."
- **Why it fails:** This is the document's only obligation about the commit *body*, and it is the one most likely to be omitted: it opens with "By the way" (an explicit aside marker), sits in a section titled `## Notes` after two sections that contain no rules section either, and bundles the obligation with its rationale ("reviewers have flagged its absence in the past") in a single sentence. An agent that has already drafted a subject line per lines 9 and 16 has no structural cue that a further requirement is waiting in the notes. The obligation is atomic (one condition — before opening a PR — and one required artifact — a "Test plan" section describing verification), so R4 does not apply, and it is checkable against the commit body, so R3 does not apply.
- **Severity:** material.
- **Suggested rewrite:** Move it into the `## Rules` section as its own item and place the rationale in context:
  - Rule: "Before opening a pull request, include a \"Test plan\" section in the commit body that describes how the change was verified."
  - Context (stays in `## Notes` or `## Background`): "Reviewers have flagged missing test plans in the past."
  - Note for the author, not counted as a finding: the rewrite preserves "the commit body" as written. If the intent is that every commit in a multi-commit PR carries a test plan (rather than at least one), state that explicitly; the audit does not choose.

## Not flagged (false-positive guards)

- **Line 3, frontmatter description.** Compact surface containing only a trigger statement; it makes no behavioral demand, so there is nothing to mark inline.
- **Lines 8 and 10.** History and team sentiment — discretionary context that degrades gracefully. Correctly outside any rule section.
- **Line 14.** "Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog." Load-bearing tool semantics: losing it would leave the agent unable to see why the prefix matters, but it does not direct behavior. Correctly placed in `## Background`; it should stay out of the `## Rules` section the rewrites introduce.
- **Line 15.** Rationale for consistency — discretionary context, correctly placed.
- **Line 17.** "People joke that this is the one rule everybody breaks eventually." Discretionary flavor. It does not hedge the strength of the line 16 rule itself (which says "must never"), so it is not an R2 finding; its only effect is to compound the burial noted in Finding 2.
- **Line 22.** Tool semantics about `CHANGELOG.md` and release announcements. Not a directive; it is not a rule and is correctly outside any rule section. Whether it is load-bearing for commit drafting is doubtful, but that is a prose-relevance question outside this audit's scope.
- **R2.** All three rules carry explicit strength ("always", "must never", "must"). No hedged statements.
- **R3.** All three rules are checkable against output (message prefix, subject-line length, presence and content of a "Test plan" section in the body). No untestable directives.
- **R4.** No rule bundles independently checkable obligations; line 21 is a single condition–action unit.
- **R5.** The three rules govern different parts of the message (type prefix, subject length, body section) and cannot prescribe incompatible outcomes for the same decision. No precedence is needed.

## Safety note

None. The target contains no auditor-directed instructions that attempt to alter, suppress, or redirect the audit.

## Summary

**Counts per rule:** R1 3, R2 0, R3 0, R4 0, R5 0.
**Counts per severity:** material 3, minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity.
Safety notes: none (reported separately, excluded from counts).

The document has no rules section at all: its three binding rules — lowercase conventional-commit type prefix, 72-character subject limit, and a "Test plan" section in the commit body before opening a PR — are each buried in narrative prose under headings (`## Background`, `## Notes`, and an unlabeled intro) that signal context rather than obligation, and each is introduced with aside phrasing ("we agreed", "It's also worth noting", "By the way") or fused with its rationale. Every rule is explicit in strength, verifiable, atomic, and free of conflict with the others, so the fix is purely structural: add a `## Rules` section holding the three rules as separate items, and leave the history, rationale, and tool semantics where they are. No author decisions are required for the rewrites to preserve semantics; the one scope question noted under Finding 3 is optional clarification, not a blocker.
