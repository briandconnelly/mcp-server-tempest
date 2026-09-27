# Scenario 1 — With-Skill Confirmation Cell (final wording after Copilot review)

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
Notes: Rerun of `2026-09-26-scenario1-with-skill.md` on the final blob after the Copilot review fix; the cell's purpose is unchanged: scenario 1's three defects are found only by classifying every statement, so it is the cell for the litmus-test sentence. Each subagent transcript also carried the harness's auto-mode tool-preference reminder once (checked by grep in all fifteen transcripts of this session); every arm nonetheless made only the three tool calls its preface permitted.

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
| 1 | The arm still classifies every body statement with the litmus test and reaches all three buried rules | PASS | Heading "Surface classification"; three findings at "Location: line 9", "Location: line 16", "Location: line 21" |
| 2 | Same | PASS | Heading "Surface classification"; same three locations |
| 3 | Same | PASS | Heading "Surface classification (R1)"; same three locations |

## Result on the scenario's standing assertions

| Rep | 1: conventional-commit clause, R1 | 2: 72-character clause, R1 | 3: test-plan clause, R1 | 4: all three material | 5: no finding against background sentences | Total |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | PASS | PASS | PASS | PASS ("material 3 (R1, R1, R1), minor 0") | PASS | 5/5 |
| 2 | PASS | PASS | PASS | PASS ("material 3 (R1, R1, R1), minor 0") | PASS | 5/5 |
| 3 | PASS | PASS | PASS | PASS ("material 3 (R1, R1, R1), minor 0") | PASS | 5/5 |

Per-rule counts are "R1 3, R2 0, R3 0, R4 0, R5 0" in all three reps, and each rep's rewrites move the three rules into a new `## Rules` section.

Observations outside the assertions, recorded for issue #161 (E9):

- All three reps appended an unrequested rewritten document, and all three reword the protected "People joke" sentence inside it (rep 1: "People joke that the length limit is the one rule everybody breaks eventually."; rep 2: "People joke that the subject-length limit is the one rule everybody breaks eventually."; rep 3: "People joke that the 72-character limit is the one rule everybody breaks eventually."). Across the three cells on this fixture, unrequested rewrites are 8/9 (2026-09-14 3/3, `2cf05a1` 2/3, this cell 3/3) and the protected sentence is reworded in 7/9 (3/3, 1/3, 3/3), with no pattern by wording.
- No rep labeled the test-plan scope as an author decision with alternatives; each kept "the commit body" as written and noted the multi-commit question as optional. That was 1/3 on 2026-09-14 and 2/3 on `2cf05a1`, so it is not stable at three reps on any wording and is not attributed to the edit.

## Scored Output — rep 1

sha256 of the raw report: `68843d8a602adf9804a6260efa0d0dc4d8d72766d3de5acc4444ac528a7c09c9`

# Audit: `commit-message-helper` — separation of context from constraints

Line numbers count the target document from its opening `---` as line 1 (blank lines included).

## Surface classification

- **Frontmatter `description` (line 3)**: compact surface (a single inline field). "Use when drafting commit messages for this repo." is an imperative trigger condition. Its binding content is marked inline, so it passes R1. No findings.
- **Body (lines 6–22)**: a standalone document of more than one paragraph, so it is long-form. Under R1 its rules belong in a dedicated labeled section. The body has no such section: its only headings are `## Background` and `## Notes`, and all three of its binding rules sit inside narrative prose.

## Statement classification (litmus test)

| Line | Statement (abridged) | Role |
|---|---|---|
| 3 | "Use when drafting commit messages for this repo." | Binding (trigger), compact surface |
| 8 | "This repository has accumulated commit history from several tools…" | Discretionary context |
| 9 | "When we finally settled the convention… we agreed messages should always start with a lowercase conventional-commit type such as feat or fix." | Binding rule wrapped in history (discretionary) |
| 10 | "The team has been happy with this approach since adoption." | Discretionary context |
| 14 | "Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog." | Load-bearing fact |
| 15 | "Contributors sometimes ask why we care so much about formatting…" | Discretionary context (rationale) |
| 16 | "It's also worth noting that the subject line must never exceed 72 characters, since…" | Binding rule plus rationale |
| 17 | "People joke that this is the one rule everybody breaks eventually." | Discretionary context |
| 21 | "By the way, before you open a pull request the commit body must include a "Test plan" section…" | Binding rule plus rationale |
| 22 | "The release-notes generator reads the `CHANGELOG.md` file at the repo root…" | Load-bearing fact |

## Findings

**R1 Distinguishability**
Location: line 9 (untitled introductory paragraph).
Quoted text: "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
Why it fails: this is the document's core formatting rule, but it is written as reported history ("we agreed") inside a narrative paragraph about how the convention came about. It sits between two sentences of pure flavor (lines 8 and 10). This long-form document has no rules section, and nothing about where the sentence sits tells the reader that it binds today rather than recounting a past decision. The strength itself is clear ("should always"), and line 10 confirms the convention is still in force, so the defect is placement, not R2.
Severity: material.
Suggested rewrite: add a `## Rules` section and state the rule there as its own item: "Start every commit message with a lowercase conventional-commit type, such as `feat` or `fix`." Keep the history as context, for example in `## Background`: "This repository has accumulated commit history from several tools, and message style drifted until the convention was settled during the 2023 tooling cleanup. The team has been happy with it since adoption."

**R1 Distinguishability**
Location: line 16 (`## Background`).
Quoted text: "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
Why it fails: a mandatory rule ("must never") is introduced with an aside ("It's also worth noting"), placed in `## Background`, and fused with its rationale in the same sentence. The next sentence (line 17, "the one rule everybody breaks eventually") is flavor that makes the rule sound negotiable. As placed, nothing separates the requirement from the commentary around it.
Severity: material.
Suggested rewrite: move the obligation into `## Rules` as its own item: "Keep every commit subject line to 72 characters or fewer." Leave the rationale in `## Background`: "Several terminal-based git tools truncate or wrap subject lines longer than 72 characters awkwardly during review." Line 17 can stay in `## Background` as discretionary context, or the author can drop it. This audit does not require either choice.

**R1 Distinguishability**
Location: line 21 (`## Notes`).
Quoted text: "By the way, before you open a pull request the commit body must include a "Test plan" section describing how the change was verified — reviewers have flagged its absence in the past."
Why it fails: a mandatory rule ("must include") is introduced as an aside ("By the way"), placed in a `## Notes` section next to a tool-semantics fact, and joined to its rationale by a dash. A reader skimming for requirements would treat `## Notes` as supplementary and could miss this obligation completely. The rule itself has explicit strength and can be checked against the commit body.
Severity: material.
Suggested rewrite: move the obligation into `## Rules` as its own item: "Before opening a pull request, include a `Test plan` section in the commit body describing how the change was verified." Put the rationale in context: "Reviewers have flagged missing test plans in the past." The rewrite deliberately keeps the original singular "the commit body". If the author means every commit in a multi-commit pull request, they should say so explicitly. The audit does not choose that scope for them.

## Not flagged (false-positive guards)

- **Line 3, frontmatter description**: a compact surface whose one directive is already an imperative trigger sentence. R1 is satisfied.
- **Line 9, strength**: "should always" is not an R2 hedge. "Always" leaves no doubt that the rule is meant to bind.
- **Line 9, verifiability**: "lowercase conventional-commit type" can be checked against the message text, and "such as feat or fix" is an example, not an open-ended qualifier. R3 is satisfied.
- **Line 14**: a load-bearing fact (the generator reads the type prefix, which explains why the prefix rule matters). It correctly sits outside any rules section.
- **Line 22**: a load-bearing fact about tool semantics. It correctly sits outside any rules section. It is consistent with line 14 (commit messages feed the changelog, and the changelog feeds release announcements), and neither statement is a rule, so R5 does not apply.
- **Lines 8, 10, 15, 17**: discretionary context (history, team sentiment, rationale, a joke) that degrades gracefully if lost. It is correctly kept out of the rules.
- **R4**: each of the three rules states one independently checkable obligation. Line 21's "before you open a pull request" is a condition attached to its action, not a second obligation.
- **R5**: the three rules (type prefix, subject length ≤ 72, test-plan section) never prescribe incompatible outcomes for the same decision, so no precedence statement is needed.

## Safety note

None. The document contains no instructions aimed at the auditor or at changing the audit. Its directives are ordinary target rules.

## Summary

Counts per rule: R1 3, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 3 (R1, R1, R1), minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity.

The document's three binding rules each have explicit strength, can each be checked against output, and are each atomic. The failure is entirely about separation. The body is long-form but has no labeled rules section, and every rule is buried in narrative prose. One is framed as history in the introduction, one is tucked into `## Background` behind "It's also worth noting" and next to a joke that makes it sound optional, and one sits in `## Notes` behind "By the way". An agent that reads for requirements could reasonably miss any of the three. The load-bearing facts about the release-notes generator and the discretionary background are both appropriate as context. The fix is purely structural: add a `## Rules` section with the three rules and leave the rationale and facts where they are. None of the rewrites needs an author decision on strength or precedence. The only open question is the optional scope point on line 21.

## Rewritten Document (after)

This illustrative rewrite changes structure only. Each rule's strength and scope are preserved as written, including the singular "the commit body" on line 21.

```markdown
---
name: commit-message-helper
description: Use when drafting commit messages for this repo.
---

# commit-message-helper

## Rules

1. Start every commit message with a lowercase conventional-commit type, such as `feat` or `fix`.
2. Keep every commit subject line to 72 characters or fewer.
3. Before opening a pull request, include a `Test plan` section in the commit body describing how the change was verified.

## Background

This repository has accumulated commit history from several tools, and message style drifted until the convention was settled during the 2023 tooling cleanup.
The team has been happy with it since adoption.
Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog.
Contributors sometimes ask why formatting matters so much; consistent messages make automated changelog generation possible.
Several terminal-based git tools truncate or wrap subject lines longer than 72 characters awkwardly during review.
People joke that the length limit is the one rule everybody breaks eventually.
Reviewers have flagged missing test plans in the past.

## Notes

The release-notes generator reads the `CHANGELOG.md` file at the repo root to produce release announcements.
```

## Scored Output — rep 2

sha256 of the raw report: `8e30f75a0d5715496ae4d0da6abbb19ffdaa24db50baf32860b617d09163052b`

# Audit: commit-message-helper — separation of context from constraints

Line numbers refer to the target document as given, counting the opening `---` as line 1.

## Surface classification

- **Frontmatter `description` (line 3)** — compact surface. "Use when drafting commit messages for this repo." is a trigger condition that informs when the skill applies; it carries no binding rule to mark. Not flagged.
- **Body (lines 6–22)** — a standalone document of more than one paragraph, so it is long-form under R1 and its rules belong in a dedicated labeled section. The body has no such section: it has only an untitled intro paragraph, `## Background`, and `## Notes`. All three of its binding rules sit inside narrative prose.

## Statement classification

| Line | Statement (abridged) | Role |
|---|---|---|
| 8 | "This repository has accumulated commit history from several tools…" | Discretionary context |
| 9 | "…we agreed messages should always start with a lowercase conventional-commit type such as feat or fix." | **Binding rule** (inside a history sentence) |
| 10 | "The team has been happy with this approach since adoption." | Discretionary context |
| 14 | "Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog." | Load-bearing fact |
| 15 | "Contributors sometimes ask why we care so much about formatting…" | Discretionary context (rationale) |
| 16 | "…the subject line must never exceed 72 characters, since several terminal-based git tools truncate…" | **Binding rule** plus rationale |
| 17 | "People joke that this is the one rule everybody breaks eventually." | Discretionary context |
| 21 | "By the way, before you open a pull request the commit body must include a "Test plan" section… — reviewers have flagged its absence in the past." | **Binding rule** plus rationale |
| 22 | "The release-notes generator reads the `CHANGELOG.md` file at the repo root to produce release announcements." | Load-bearing fact |

## Findings

**R1 Distinguishability**
Location: line 9.
Quoted text: "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
Why it fails: this is the skill's central binding rule, but it appears as the reported outcome of a past decision ("we agreed…") in the middle of an untitled history paragraph, between two sentences of discretionary context. Nothing about where it sits or how it is framed shows that it binds the agent now, and the long-form body has no rules section to hold it. Its strength is clear ("always"), so this is not an R2 issue. The defect is where the rule sits and how it is framed.
Severity: material.
Suggested rewrite: add a `## Rules` section and state it there as its own item: "Always start the commit message with a lowercase conventional-commit type, such as `feat` or `fix`." Keep the history in context: "The commit-message convention was settled during the 2023 tooling cleanup, and the team has been happy with it since adoption."

**R1 Distinguishability**
Location: line 16.
Quoted text: "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
Why it fails: a mandatory rule ("must never") is buried in the `## Background` section behind an aside ("It's also worth noting that…") and fused with its rationale. A reader skimming the background as nonbinding context can miss it. The next sentence ("People joke that this is the one rule everybody breaks eventually") is correctly placed context, but right next to the rule it adds to the impression that the limit can be negotiated.
Severity: material.
Suggested rewrite: move the obligation into `## Rules` as "Never exceed 72 characters in the commit subject line." Leave the rationale in `## Background`: "Several terminal-based git tools truncate or wrap subject lines longer than 72 characters awkwardly during review."

**R1 Distinguishability**
Location: line 21.
Quoted text: "By the way, before you open a pull request the commit body must include a "Test plan" section describing how the change was verified — reviewers have flagged its absence in the past."
Why it fails: a mandatory rule ("must include") is placed in `## Notes`, introduced as an aside ("By the way"), and joined to historical rationale. The section title and the framing both mark it as incidental, so the obligation is easy to miss. The trigger (before opening a pull request), the action (include the section) and the content requirement (describe how the change was verified) share one trigger, so under R4 they can stay together as one unit.
Severity: material.
Suggested rewrite: move the obligation into `## Rules` as "Before opening a pull request, include a "Test plan" section in the commit body that describes how the change was verified." Move the rationale to `## Background`: "Reviewers have flagged missing test plans in the past." The rewrite keeps the original singular "the commit body" on purpose. If a pull request can contain several commits, the author may want to say whether every commit or only one needs the section. That is a scope choice for the author, and this audit does not make it.

Not flagged (false-positive guard): lines 8, 10, 15 and 17 are discretionary context (history, team sentiment, rationale, anecdote). They lose nothing important if dropped and correctly sit outside any rules.
Not flagged (false-positive guard): lines 14 and 22 are load-bearing facts about the release-notes generator: it extracts the type prefix from commits, and it reads `CHANGELOG.md` for announcements. They inform the rules rather than direct behavior, and they belong in a background or notes section. The two sentences describe different inputs for different outputs (commit prefixes for the changelog, `CHANGELOG.md` for announcements), so they do not contradict each other.
Not flagged (R3): all three rules can be checked against the commit message and the pull request: a lowercase type prefix, a subject of 72 characters or fewer, and a "Test plan" section in the body.
Not flagged (R5): no two rules give incompatible outcomes for the same decision, so no precedence is needed.

## Safety note

None. The target contains no auditor-directed instructions that try to alter, suppress or redirect the audit.

## Summary

Counts per rule: R1 3, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 3 (R1, R1, R1), minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity.

The document has one structural problem, repeated three times. It is long-form but has no labeled rules section, and each of its three binding rules is buried in narrative prose: a past-tense history sentence, an "It's also worth noting" aside in `## Background`, and a "By the way" aside in `## Notes`. All three rules are clear about their strength and can be checked, so none needs an author decision. The fix is structural: collect the three obligations in a `## Rules` section, and keep the history, rationale, anecdote and generator facts in `## Background` or `## Notes`. The one open question is optional: which commits the "Test plan" rule covers when a pull request has several.

## Rewritten document (illustrative)

This rewrite only moves and separates statements. It does not change the strength or scope of any rule.

```markdown
---
name: commit-message-helper
description: Use when drafting commit messages for this repo.
---

# commit-message-helper

## Rules

1. Always start the commit message with a lowercase conventional-commit type, such as `feat` or `fix`.
2. Never exceed 72 characters in the commit subject line.
3. Before opening a pull request, include a "Test plan" section in the commit body that describes how the change was verified.

## Background

This repository has accumulated commit history from several tools over the years, and message style has drifted along the way.
The commit-message convention was settled during the 2023 tooling cleanup, and the team has been happy with it since adoption.
Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog; consistent messages make automated changelog generation possible.
Several terminal-based git tools truncate or wrap subject lines longer than 72 characters awkwardly during review.
People joke that the subject-length limit is the one rule everybody breaks eventually.
Reviewers have flagged missing test plans in the past.

## Notes

The release-notes generator reads the `CHANGELOG.md` file at the repo root to produce release announcements.
```

## Scored Output — rep 3

sha256 of the raw report: `22feb82f30b10f08eb819425da43f7482bd853fb4efedfb69b3df63479792a27`

# Audit: `commit-message-helper` — separation of context from constraints

Line numbers count the target document from its opening frontmatter `---` as line 1.

## Surface classification (R1)

- **Frontmatter `description`** (line 3): compact surface. "Use when drafting commit messages for this repo." is a trigger condition and carries no buried rule. Clean.
- **Body** (lines 6–22): standalone document with more than one paragraph, so it is long-form. R1 requires its rules to sit in a dedicated labeled section. The body has no such section: it has an untitled intro, `## Background`, and `## Notes`. All three of its binding rules sit inside narrative or context prose.

## Statement classification

| Line | Statement (abridged) | Class |
|---|---|---|
| 8 | "accumulated commit history from several tools… style has drifted" | Discretionary context |
| 9 | "…we agreed messages should always start with a lowercase conventional-commit type such as feat or fix." | Binding rule (buried in history) |
| 10 | "The team has been happy with this approach since adoption." | Discretionary context |
| 14 | "Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog." | Load-bearing fact |
| 15 | "Contributors sometimes ask why… consistent messages make automated changelog generation possible." | Discretionary context (rationale) |
| 16 | "…the subject line must never exceed 72 characters, since several terminal-based git tools truncate…" | Binding rule (buried in Background) plus rationale |
| 17 | "People joke that this is the one rule everybody breaks eventually." | Discretionary context |
| 21 | "By the way, before you open a pull request the commit body must include a 'Test plan' section… — reviewers have flagged its absence in the past." | Binding rule (buried in Notes) plus rationale |
| 22 | "The release-notes generator reads the `CHANGELOG.md` file at the repo root to produce release announcements." | Load-bearing fact |

## Findings

**R1 Distinguishability**
Location: line 9 (untitled intro paragraph).
Quoted text: "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
Why it fails: this is the skill's central formatting rule, but it is written as reported history ("when we finally settled… we agreed") in the middle of a narrative intro. It sits between two sentences of background (lines 8 and 10). Nothing about where it sits marks it as a current directive, and the document has no rules section to hold it. The strength itself is clear ("always"), so moving it into a rules section does not change policy.
Severity: material.
Suggested rewrite: put it in a new `## Rules` section as its own item: "Start every commit message with a lowercase conventional-commit type, such as `feat` or `fix`." Keep the history in context: "The convention was settled during the 2023 tooling cleanup."

**R1 Distinguishability**
Location: line 16 (`## Background`).
Quoted text: "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
Why it fails: a mandatory rule ("must never") sits inside the `## Background` section. It is introduced as an aside ("It's also worth noting"), which presents it as a side remark. The rule and its rationale are fused into one sentence. The next line, the joke that "everybody breaks" this rule, sits right beside it and makes it harder to tell negotiable flavor from a requirement.
Severity: material.
Suggested rewrite: split the sentence. Add the rule to `## Rules`: "Never exceed 72 characters in the subject line." Leave the rationale in `## Background`: "Several terminal-based git tools truncate or wrap subject lines longer than 72 characters awkwardly during review."

**R1 Distinguishability**
Location: line 21 (`## Notes`).
Quoted text: "By the way, before you open a pull request the commit body must include a \"Test plan\" section describing how the change was verified — reviewers have flagged its absence in the past."
Why it fails: a mandatory rule ("must include") with its own trigger ("before you open a pull request") is buried in a `## Notes` section. It is introduced as an aside ("By the way") and placed next to a tool-semantics fact (line 22). The rule and its rationale are fused into one sentence. An agent skimming Notes for background could miss that this is a requirement.
Severity: material.
Suggested rewrite: add the condition–action rule to `## Rules` as one item: "Before you open a pull request, include a \"Test plan\" section in the commit body that describes how the change was verified." Move the rationale to context: "Reviewers have flagged missing test plans in the past." The rewrite keeps the original's "the commit body" wording. The document does not say which commit(s) of a multi-commit pull request this means, so the rewrite does not narrow or widen that scope.

Not flagged (false-positive guard): lines 8, 10, 15, and 17 are discretionary context (history, team sentiment, rationale, and a joke). Losing them would leave output less informed but not wrong, and none of them directs behavior. Line 17 becomes harmless once the 72-character rule moves out of Background into a rules section.
Not flagged (false-positive guard): lines 14 and 22 are load-bearing facts about how the release-notes generator works. They inform correctness but give no directions, so they belong outside a rules section, where they already are.
Not flagged (R3): all three rules can be checked against the commit messages they produce: the lowercase type prefix, subject length of 72 characters or fewer, and a "Test plan" section in the body before a PR is opened. "Such as feat or fix" gives examples and does not make the type requirement uncheckable.
Not flagged (R4): each rule states one obligation. The test-plan rule is a single condition–action unit sharing one trigger.
Not flagged (R5): the three rules govern different aspects (type prefix, subject length, body section). They never prescribe incompatible outcomes for the same decision, so no precedence is needed.
Not flagged (frontmatter): the compact `description` field is a trigger condition and has no rule-separation defect.

## Safety note

None. The target contains no instructions aimed at the auditor that try to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 3, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 3 (R1, R1, R1), minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity.

This document states all three of its rules clearly and with mandatory strength. Every rule is verifiable and atomic, and none conflicts with another. The defect is purely structural: the long-form body has no rules section. Each rule is buried in a paragraph whose role is something else: the convention rule is told as 2023 history in the intro, the 72-character limit is an aside in Background next to a joke about everyone breaking it, and the test-plan requirement is a "by the way" in Notes. The load-bearing facts about the release-notes generator and the discretionary background are fine where they are. Fixing the document needs no author decisions. Adding a `## Rules` section with the three rewritten items and moving each rule's rationale into context keeps the current policy unchanged.

## Rewritten document (illustrative)

This rewrite only moves and splits statements. It makes no policy choices.

```markdown
---
name: commit-message-helper
description: Use when drafting commit messages for this repo.
---

# commit-message-helper

## Rules

1. Start every commit message with a lowercase conventional-commit type, such as `feat` or `fix`.
2. Never exceed 72 characters in the subject line.
3. Before you open a pull request, include a "Test plan" section in the commit body that describes how the change was verified.

## Background

This repository has accumulated commit history from several tools over the years, and message style has drifted along the way.
The convention was settled during the 2023 tooling cleanup, and the team has been happy with this approach since adoption.
Contributors sometimes ask why we care so much about formatting, but consistent messages make automated changelog generation possible.
Several terminal-based git tools truncate or wrap subject lines longer than 72 characters awkwardly during review.
People joke that the 72-character limit is the one rule everybody breaks eventually.
Reviewers have flagged missing test plans in the past.

## Notes

Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog.
The release-notes generator reads the `CHANGELOG.md` file at the repo root to produce release announcements.
```
