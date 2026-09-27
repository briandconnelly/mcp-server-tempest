# Scenario 1 — With-Skill Confirmation Cell, PR #169 Wording

Date: 2026-09-14
Run: with-skill
SKILL.md blob: 713c6967362667a405048a7e75d04f18c329804c
Commit: none — run against the uncommitted working tree on branch `fix/context-constraints-r1-r3-and-rescore-evidence` (head `ca61abe` plus the review-round edits committed with this artifact)
Referenced files: references/example-audit.md f825b78fff6df83c0218ac30f7c020a1c142942b
Model: claude-fable-5-1, the session model at dispatch, inherited by each subagent with no per-agent override
Harness: Claude Code 2.1.272, Agent tool, general-purpose subagent, three independent dispatches in one parallel batch
Prompt: the scenario 1 prompt from `tests/scenarios.md`, verbatim, preceded by the preface quoted under "Dispatch" below
Sampling: harness default
Scorer: Claude Opus 5 (claude-opus-5), the session model after a mid-session switch, 2026-09-14, unblinded; the arms ran on a different model than the scorer
Notes: Confirmation cell for the PR #169 R1 surface-classification change. All three reps wrote and handed back complete reports; the harness then marked each subagent failed on a rate-limit error raised after its hand-back.

The scratchpad copies of the raw reports were removed by system temp cleanup on 2026-09-19, after this artifact was written.
Each scored output embedded below was then verified byte-identical to the `Write` tool input recovered from that arm's task transcript, and the recorded digests match those recoveries.

## Why this cell

PR #169 replaced R1's "labeled sections or rules distributed across multiple paragraphs" test with a surface-first one.
A target may carry several surfaces, each classified separately, and a standalone document of more than one paragraph is long-form.
Scenario 1 is the R1 cell: a skill file whose frontmatter description and body are separate surfaces, with three rules buried in the body's narrative.
Its body has headings, so this cell checks the old path still reaches long-form under the new wording.
It does not exercise the newly covered sectionless multi-paragraph case, which has no fixture yet.

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
| 1 | Frontmatter and body classified separately; body long-form by the standalone-document clause | PASS | "Frontmatter `description` (line 3): a single inline field, so it is compact." / "Body (lines 6–22): a standalone document of more than one paragraph, so it is long-form." |
| 2 | Same | PASS | "**Frontmatter `description` (line 3)** — compact surface." / "**Body (lines 6–22)** — a standalone document of more than one paragraph, so long-form." |
| 3 | Same | PASS | "Frontmatter `description` (line 3) — compact surface." / "Body (lines 6–22) — a standalone document of several paragraphs, so long-form." |

## Result on the scenario's standing assertions

| Rep | 1: conventional-commit clause, R1 | 2: 72-character clause, R1 | 3: test-plan clause, R1 | 4: all three material | 5: no finding against background sentences | Total |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | PASS | PASS | PASS | PASS ("material 3, minor 0") | PASS | 5/5 |
| 2 | PASS | PASS | PASS | PASS ("material 3, minor 0") | PASS | 5/5 |
| 3 | PASS | PASS | PASS | PASS ("material 3 (R1, R1, R1), minor 0") | PASS | 5/5 |

Each rep's three R1 findings quote the clause, locate it, and rewrite it into a new `## Rules` section.
Each rep lists the "People joke" and `CHANGELOG.md` sentences as not flagged.

Two observations fall outside the assertions.
Every rep appended an unrequested full rewritten document, and each rewords the protected "People joke" sentence there; assertion 5 scores findings only, so this is unscored.
This is the report-shape behavior draft PR #165 measures as E9.
Rep 2 also marked the test-plan rule's scope, every commit or the pull request's commit, as an author decision inside its third finding.

## Scored Output — rep 1

sha256 of the raw report: `7c1df0fd6f7c752efb8cc8311c2a89cd17baeb0ba2160fed4bdd2ea4bd0fc60a`

# Audit: commit-message-helper

Audit of the `commit-message-helper` skill for separation of binding rules from context, per `separating-context-from-constraints`.
Line numbers refer to the target as presented (line 1 is the opening `---`).

## Surface classification

The target carries two instruction-bearing surfaces.

- Frontmatter `description` (line 3): a single inline field, so it is compact.
  Its one instruction ("Use when drafting commit messages for this repo.") is an imperative trigger sentence, which is the correct inline marking for a compact surface.
  No finding.
- Body (lines 6–22): a standalone document of more than one paragraph, so it is long-form.
  Long-form surfaces place their rules in a dedicated labeled section.
  The body has `## Background` and `## Notes` but no rules section at all; every binding rule it contains is embedded in narrative prose.

## Statement classification (body)

| Line | Statement (abbreviated) | Class |
|---|---|---|
| 8 | History has drifted across tools | Discretionary context |
| 9 | "...we agreed messages should always start with a lowercase conventional-commit type such as feat or fix." | **Binding rule** |
| 10 | Team has been happy since adoption | Discretionary context |
| 14 | Release-notes generator extracts the type prefix to build the changelog | Load-bearing fact |
| 15 | Consistent messages make changelog generation possible | Discretionary context (rationale) |
| 16 | "...the subject line must never exceed 72 characters, since..." | **Binding rule** (with rationale attached) |
| 17 | People joke everybody breaks this rule | Discretionary context |
| 21 | "...the commit body must include a "Test plan" section describing how the change was verified — reviewers have flagged..." | **Binding rule** (with rationale attached) |
| 22 | Generator reads `CHANGELOG.md` at repo root | Load-bearing fact |

## Findings

**R1 Distinguishability**
Location: line 9 (untitled opening paragraph).
Quoted text: "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
Why it fails: this is the document's primary binding rule — the required form of every commit message — but it is delivered as the second half of a sentence about 2023 history, framed as a past agreement ("we agreed") rather than a present directive, and sandwiched between two sentences of discretionary color (lines 8 and 10).
Nothing in its placement signals that it binds; an agent skimming for requirements can read the whole paragraph as background.
Strength is not in question ("always" is unambiguous), so no R2 id is carried.
Severity: material.
Suggested rewrite: create a `## Rules` section and add as its own item: "Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`)."
Leave the history sentence in place, trimmed of the rule: "When we settled the convention during the 2023 tooling cleanup, we standardized on conventional-commit type prefixes."

**R1 Distinguishability**
Location: line 16 (`## Background`).
Quoted text: "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
Why it fails: this is a binding rule with clear strength ("must never") and a checkable threshold, but it sits in a section labeled `## Background`, is introduced with "It's also worth noting" — phrasing that marks an aside, not a requirement — and is immediately followed by line 17, which tells the reader everybody breaks it.
The section label and the framing both say "context"; only the modal verb says "rule".
Severity: material.
Suggested rewrite: move to `## Rules` as its own item: "Keep the subject line to 72 characters or fewer."
Keep the rationale in `## Background`: "Several terminal-based git tools truncate or wrap subject lines longer than 72 characters during review."
Line 17 may stay in `## Background` as discretionary context; it no longer sits next to the rule it undercuts.

**R1 Distinguishability**
Location: line 21 (`## Notes`).
Quoted text: "By the way, before you open a pull request the commit body must include a "Test plan" section describing how the change was verified — reviewers have flagged its absence in the past."
Why it fails: this is a binding rule ("must include") with a checkable artifact (a `Test plan` section in the commit body), but it is opened with "By the way" — the strongest possible signal that what follows is optional — and placed in `## Notes` alongside a tool-semantics fact.
The rationale after the dash is fused to the rule in one sentence.
Severity: material.
Suggested rewrite: move to `## Rules` as its own item, preserving the original trigger wording: "Before opening a pull request, include a `Test plan` section in the commit body describing how the change was verified."
Keep the rationale in `## Notes` or `## Background`: "Reviewers have flagged missing Test plan sections in the past."
The original does not say whether every commit in the pull request or only the commit being drafted needs the section; the rewrite preserves that wording rather than resolving it, since choosing a scope would change policy.

## Not flagged (false-positive guards)

- Line 3, the `description` field: a compact surface whose single trigger instruction is already marked with an imperative; correctly formed.
- Lines 8, 10, 15, 17: discretionary context — history, morale, rationale, humor — placed outside any rule section; correct placement, no change needed.
- Line 14, the type-prefix extraction fact: load-bearing (losing it obscures why the prefix rule exists and how it is consumed), but it does not direct behavior, so it correctly stays in `## Background`.
- Line 22, the `CHANGELOG.md` fact: load-bearing tool semantics, not a directive; correctly outside a rule section.
- Line 9, "lowercase conventional-commit type": two attributes (case, vocabulary) of one prefix under one trigger.
  This is a single obligation about the form of one token, not a bundle of independent actions, so R4 is not carried.
- R2: none of the three rules hedges strength; "should always", "must never", and "must include" each bind unambiguously.
- R3: all three rules are checkable against output — the leading token's case and vocabulary, the subject-line character count, and the presence and content of a `Test plan` section in the body.
- R5: the three rules govern different parts of the message (type prefix, subject length, body section) and cannot prescribe incompatible outcomes on any input; no precedence is needed.

## Safety note

None.
The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 3, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 3, minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity.
Safety notes: none (excluded from counts).

The document has one structural defect expressed three times: it contains three binding rules and no rules section, so each rule is carried by narrative prose whose framing ("we agreed", "It's also worth noting", "By the way") actively signals that it does not bind.
The rules themselves are well formed — each has unambiguous strength, a checkable obligation, and a single atomic requirement, and none conflicts with another — which is why every finding is R1 alone and no author decisions are needed before rewriting.
The surrounding context is largely correct as context: the history, rationale, and two tool-semantics facts all belong outside a rules section and can stay where they are once the rules are extracted.
The fix is mechanical: add a `## Rules` section holding the three imperatives and leave the rationale behind.

## Rewritten document (after)

This rewrite makes no policy choices; it relocates the three rules and trims their rationale into the existing context sections.

```markdown
---
name: commit-message-helper
description: Use when drafting commit messages for this repo.
---

# commit-message-helper

This repository has accumulated commit history from several tools over the years, and message style has drifted along the way.
When we settled the convention during the 2023 tooling cleanup, we standardized on conventional-commit type prefixes.
The team has been happy with this approach since adoption.

## Rules

1. Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`).
2. Keep the subject line to 72 characters or fewer.
3. Before opening a pull request, include a `Test plan` section in the commit body describing how the change was verified.

## Background

Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog.
Contributors sometimes ask why we care so much about formatting, but consistent messages make automated changelog generation possible.
Several terminal-based git tools truncate or wrap subject lines longer than 72 characters during review.
People joke that the subject-line limit is the one rule everybody breaks eventually.
Reviewers have flagged missing Test plan sections in the past.

## Notes

The release-notes generator reads the `CHANGELOG.md` file at the repo root to produce release announcements.
```

## Scored Output — rep 2

sha256 of the raw report: `b7bb19b1d1d31a430774e71897499c896ee126b7d90cb60174875052595d9d0e`

# Audit: `commit-message-helper` — separation of context from constraints

Skill applied: `separating-context-from-constraints` (SKILL.md plus `references/example-audit.md`).
Line numbers refer to the target as quoted, with the opening `---` as line 1.

## Surface classification (R1)

The target carries two instruction-bearing surfaces, classified separately:

- **Frontmatter `description` (line 3)** — compact surface. It contains only a trigger condition ("Use when drafting commit messages for this repo.") and no binding rules, so there is nothing to mark inline. No finding.
- **Body (lines 6–22)** — a standalone document of more than one paragraph, so long-form. Long-form surfaces place their rules in a dedicated labeled section. The body has no rules section at all: its three binding rules sit inside an untitled intro paragraph, a `## Background` section, and a `## Notes` section, interleaved with history, rationale, tool semantics, and jokes.

## Statement classification (two-question litmus test)

| Line | Statement (abbreviated) | Directs or informs? | If lost, output wrong or less informed? | Class |
|---|---|---|---|---|
| 3 | "Use when drafting commit messages for this repo." | Informs (trigger) | Less informed | Discretionary / trigger metadata |
| 8 | History has drifted across tools | Informs | Less informed | Discretionary context |
| 9 | "messages should always start with a lowercase conventional-commit type such as feat or fix" | **Directs** | — | **Binding rule** |
| 10 | Team happy since adoption | Informs | Less informed | Discretionary context |
| 14 | Release-notes generator extracts the type prefix to build the changelog | Informs | Wrong (explains why the prefix is machine-read) | Load-bearing fact |
| 15 | Contributors ask why; consistency enables changelog automation | Informs | Less informed | Discretionary context (rationale) |
| 16 | "the subject line must never exceed 72 characters" (+ rationale clause) | **Directs** | — | **Binding rule** with attached rationale |
| 17 | "the one rule everybody breaks eventually" | Informs | Less informed | Discretionary context |
| 21 | "before you open a pull request the commit body must include a 'Test plan' section describing how the change was verified" (+ rationale clause) | **Directs** | — | **Binding rule** with attached rationale |
| 22 | Generator reads `CHANGELOG.md` at repo root | Informs | Wrong (tool semantics) | Load-bearing fact |

Three binding rules, two load-bearing facts, five discretionary statements. None of the three rules is structurally distinguishable from the context around it.

## Findings

### Finding 1 — R1 Distinguishability

- **Rule id:** R1
- **Location:** line 9 (untitled intro paragraph under the `# commit-message-helper` heading)
- **Quoted text:** "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
- **Why it fails:** This is the document's primary formatting rule, but it is delivered as the second half of a historical anecdote ("When we finally settled the convention during the 2023 tooling cleanup, we agreed ...") sandwiched between two sentences of pure history (lines 8 and 10). Nothing in its placement signals that it binds; a reader skimming for requirements sees a paragraph about how the convention came to be, not a directive. The strength is recoverable ("always"), so this is not an R2 finding, but the narrative framing ("we agreed ... should") reads as a report of a past agreement rather than a present obligation.
- **Severity:** material — the rule could plausibly be missed, and if missed the release-notes generator (line 14) cannot extract a type prefix.
- **Suggested rewrite:** Create a `## Rules` section and place the rule there as its own item, in the imperative: "Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`)." Leave the history in place as context: "The convention was settled during the 2023 tooling cleanup." The rewrite preserves semantics; "such as feat or fix" remains illustrative rather than an exhaustive list, exactly as in the original.

### Finding 2 — R1 Distinguishability

- **Rule id:** R1
- **Location:** line 16 (`## Background` section)
- **Quoted text:** "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
- **Why it fails:** The rule's strength is explicit ("must never") and it is verifiable against output (a character count), but it is introduced with "It's also worth noting that" — an aside marker — inside a section titled `## Background`, between a rationale sentence about why formatting matters (line 15) and a joke that everybody breaks this rule (line 17). The section heading tells the reader this is context; the framing tells the reader it is an afterthought; the following sentence tells the reader it is routinely violated. The rule's placement actively works against it being read as a requirement. The trailing "since ..." clause is rationale (discretionary context) fused to the rule in one sentence.
- **Severity:** material — a rule labeled as background and bracketed by commentary is one an agent can plausibly skip while faithfully following the document's flavor.
- **Suggested rewrite:** Move the obligation into the `## Rules` section as its own item: "Keep the subject line to 72 characters or fewer." Keep the rationale in `## Background`, unchanged in meaning: "Several terminal-based git tools truncate or wrap subject lines longer than 72 characters awkwardly during review." Line 17 may stay in Background as color (see false-positive guard below).

### Finding 3 — R1 Distinguishability

- **Rule id:** R1
- **Location:** line 21 (`## Notes` section)
- **Quoted text:** "By the way, before you open a pull request the commit body must include a \"Test plan\" section describing how the change was verified — reviewers have flagged its absence in the past."
- **Why it fails:** This is a binding rule ("must include") opening with "By the way" — a phrase that explicitly marks what follows as incidental — placed in a `## Notes` section whose only other content is a tool-semantics fact about the release-notes generator. Neither the section title nor the framing signals that a requirement is being stated. The trailing "reviewers have flagged its absence in the past" is rationale fused to the rule. The rule also has an unresolved scope ambiguity that blocks a single semantic-preserving rewrite: "the commit body" does not say whether every commit in the pull request, or only the pull request's final/squashed commit, must carry the section. That ambiguity is not an R3 defect — whichever reading is intended, satisfaction is checkable against repository state — but it must be settled before the rule can be restated without silently changing policy.
- **Severity:** material — an obligation introduced with "By the way" in a Notes section is precisely the kind of rule an agent follows the document's tone past; missing it omits a reviewer-enforced obligation.
- **Suggested rewrite:** Move the obligation into the `## Rules` section. The scope is an author decision; both alternatives preserve the stated strength and content requirement:
  - **Alternative A (every commit):** "Every commit body must include a \"Test plan\" section describing how the change was verified."
  - **Alternative B (the pull request's commit):** "Before opening a pull request, ensure the commit body of the change being submitted includes a \"Test plan\" section describing how the change was verified."
  Keep the rationale as context in `## Notes` or `## Background`: "Reviewers have flagged the absence of a Test plan section in the past."
  The auditor does not select between A and B.

## Not flagged (false-positive guards)

- **Line 3, frontmatter description:** a trigger condition on a compact surface, not a rule; nothing to mark inline.
- **Lines 8 and 10, history and team sentiment:** discretionary context that degrades gracefully if lost; correctly outside any rules section.
- **Line 14, generator extracts the type prefix:** load-bearing fact about tool semantics. Losing it would leave the type-prefix rule unexplained but it does not direct behavior, so it correctly belongs in `## Background`, not in rules.
- **Line 15, contributor questions and the automation rationale:** discretionary rationale; correctly placed.
- **Line 17, "People joke that this is the one rule everybody breaks eventually":** discretionary context. It sits beside the 72-character rule and could be read as tacit tolerance, but it does not itself hedge the rule's stated strength ("must never" is unambiguous), so it is not an R2 finding. Once the rule moves to a `## Rules` section (Finding 2) the joke can no longer be mistaken for a qualifier on it.
- **Line 22, generator reads `CHANGELOG.md`:** load-bearing tool-semantics fact; correctly outside rules. It does not conflict with line 14 (the generator extracts prefixes to build the changelog and then reads the changelog to produce announcements); in any case R5 concerns conflicting rules, and neither statement is a rule.
- **R2 on line 9:** "should always" carries "always", which fixes the strength as mandatory; not the "generally"/"try to" pattern that leaves binding status unclear.
- **R3 on line 9:** "such as feat or fix" does not enumerate the permitted types, but the obligation — a lowercase conventional-commit type — is checkable against output and the conventional-commits type set; spelling out the list is a completeness question, not a separation defect.
- **R4 on line 21:** "before you open a pull request" (trigger), "must include a Test plan section" (action), and "describing how the change was verified" (content qualifier on that section) form one condition–action unit with a single trigger, so they may stay together. The scope ambiguity is handled in Finding 3 as an author decision rather than as a bundling defect.
- **R5:** the three rules (type prefix, 72-character subject, Test plan section) govern disjoint parts of the message and cannot prescribe incompatible outcomes on any realistic input. No precedence statement is required.

## Safety note

None. The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit. All instructions in it are ordinary target rules addressed to the commit author.

## Summary

**Counts per rule:** R1 3, R2 0, R3 0, R4 0, R5 0.
**Counts per severity:** material 3, minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity.
Safety notes: none (excluded from counts).

The document contains exactly three binding rules and places none of them where a reader would look for a requirement: one is the payload of a historical anecdote in the intro, one is an "also worth noting" aside inside `## Background` followed by a joke about it being routinely broken, and one opens with "By the way" inside `## Notes`. Each rule's strength is explicit and each is verifiable, so the defect is purely structural — but it is material in every case because the surrounding prose actively signals "context" while the sentences themselves are obligations. The two load-bearing facts about the release-notes generator and the five discretionary sentences are all correctly placed outside any rules section and need no change. The only author decision required before a definitive rewrite is the scope of the Test plan obligation (every commit vs. the pull request's commit).

## Illustrative rewrite (after)

This rewrite assumes the author selected Alternative A for Finding 3 (every commit). That choice is a supplied assumption, not a meaning inferred by the audit.

```markdown
---
name: commit-message-helper
description: Use when drafting commit messages for this repo.
---

# commit-message-helper

## Rules

1. Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`).
2. Keep the subject line to 72 characters or fewer.
3. Every commit body must include a "Test plan" section describing how the change was verified.

## Background

This repository has accumulated commit history from several tools over the years, and message style has drifted along the way.
The convention was settled during the 2023 tooling cleanup, and the team has been happy with it since adoption.
Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog.
Contributors sometimes ask why we care so much about formatting, but consistent messages make automated changelog generation possible.
Several terminal-based git tools truncate or wrap subject lines longer than 72 characters awkwardly during review.
People joke that the subject-line limit is the one rule everybody breaks eventually.
Reviewers have flagged the absence of a Test plan section in the past.

## Notes

The release-notes generator reads the `CHANGELOG.md` file at the repo root to produce release announcements.
```

## Scored Output — rep 3

sha256 of the raw report: `977bfbac99a4cda7108897d1986cbb80c1b7f4a14f21a0757672f11d854b002b`

# Audit: commit-message-helper

Audit of the `commit-message-helper` skill against R1–R5 of separating-context-from-constraints.
Line numbers refer to the target document as supplied, counting the opening `---` of the frontmatter as line 1.

## Surfaces classified

The target carries two instruction-bearing surfaces.

- Frontmatter `description` (line 3) — compact surface. It contains a single trigger condition ("Use when drafting commit messages for this repo.") and no binding rules. Clean.
- Body (lines 6–22) — a standalone document of several paragraphs, so long-form. It has `## Background` and `## Notes` sections and no dedicated rule section, yet it carries three binding rules, each embedded mid-paragraph in narrative prose.

## Statement classification (body)

| Line | Statement (abridged) | Class |
|---|---|---|
| 8 | history has drifted across tools | discretionary context |
| 9 | "we agreed messages should always start with a lowercase conventional-commit type" | **binding rule** |
| 10 | team has been happy since adoption | discretionary context |
| 14 | release-notes generator extracts the type prefix to build the changelog | load-bearing fact (tool semantics) |
| 15 | contributors ask why; consistency enables changelog generation | discretionary context (rationale) |
| 16 | "the subject line must never exceed 72 characters" + terminal-tool rationale | **binding rule** + discretionary rationale |
| 17 | "the one rule everybody breaks eventually" | discretionary context |
| 21 | "the commit body must include a 'Test plan' section describing how the change was verified" + reviewer rationale | **binding rule** + discretionary rationale |
| 22 | generator reads `CHANGELOG.md` at repo root | load-bearing fact (tool semantics) |

## Findings

**R1 Distinguishability**
Location: line 9 (opening paragraph, under the H1).
Quoted text: "When we finally settled the convention during the 2023 tooling cleanup, we agreed messages should always start with a lowercase conventional-commit type such as feat or fix."
Why it fails: this is a binding rule — an agent that omits or capitalizes the type prefix produces a wrong commit message, and line 14 shows the release-notes generator depends on it — but it is stated as reported speech about a 2023 team agreement, sandwiched between two sentences of history and morale ("style has drifted", "the team has been happy"). Nothing structural marks it as a directive to the reader; it reads as an anecdote about how the convention came to be. Strength itself is clear ("always"), so this is a placement defect, not an R2 defect.
Severity: material — the only statement of the prefix requirement in the document is one an agent skimming for instructions can plausibly read past as backstory.
Suggested rewrite: add a `## Rules` section and place the obligation there as its own item, keeping the mandatory strength and the examples: "Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`)." Leave the history in the opening paragraph, reworded so it no longer carries the rule: "When we settled the convention during the 2023 tooling cleanup, we adopted lowercase conventional-commit type prefixes."

**R1 Distinguishability**
Location: line 16 (`## Background`).
Quoted text: "It's also worth noting that the subject line must never exceed 72 characters, since several terminal-based git tools truncate or wrap longer lines awkwardly during review."
Why it fails: "must never exceed 72 characters" is a mandatory, verifiable rule, but it sits in a section labeled `## Background`, is introduced with "It's also worth noting" (a marker of an aside), is welded to its rationale in the same sentence, and is immediately followed on line 17 by "People joke that this is the one rule everybody breaks eventually." The section label, the aside framing, and the adjacent joke together signal negotiable flavor rather than a requirement, so a reader cannot distinguish this obligation from the surrounding color commentary.
Severity: material — the rule's placement and surroundings actively invite the reader to treat it as optional, which could lead the agent to emit over-length subject lines.
Suggested rewrite: move the obligation into `## Rules` as its own item: "Keep the subject line at 72 characters or fewer." Keep the rationale in `## Background` as a separate sentence: "Several terminal-based git tools truncate or wrap subject lines longer than 72 characters during review." Line 17 may remain in `## Background` unchanged; once the rule lives in `## Rules` the joke no longer frames it.

**R1 Distinguishability**
Location: line 21 (`## Notes`).
Quoted text: "By the way, before you open a pull request the commit body must include a \"Test plan\" section describing how the change was verified — reviewers have flagged its absence in the past."
Why it fails: this is a mandatory rule ("must include") with a clear trigger (before opening a pull request) and a checkable artifact (a "Test plan" section in the commit body), but it is placed in `## Notes`, introduced with "By the way" — a marker of an afterthought — and fused with its rationale ("reviewers have flagged its absence"). The label and framing signal discretionary context, so the obligation is not structurally distinguishable from the tool-semantics note that follows it on line 22.
Severity: material — this is the only statement of the Test-plan requirement, and it is the one most likely to be missed: it appears in the last section, under a heading that signals optional information, opened by a phrase that signals a digression.
Suggested rewrite: move the obligation into `## Rules`, preserving the trigger and the content requirement: "Before opening a pull request, include a `Test plan` section in the commit body describing how the change was verified." Move the rationale to `## Background` as its own sentence: "Reviewers have flagged missing Test plan sections in the past." The rewrite preserves the original's "the commit body" wording without resolving which commit(s) it covers; that ambiguity is present in the source and is not a separation defect.

Not flagged (false-positive guard): lines 8, 10, 15, and 17 are discretionary context — history, morale, rationale, and a joke — that degrade gracefully if lost. They sit outside any rule section (the document has none) and require no move.
Not flagged (false-positive guard): line 14 (the generator extracts the type prefix) and line 22 (the generator reads `CHANGELOG.md` at the repo root) are load-bearing facts about tool semantics. Losing them would make the agent's understanding wrong, but they direct nothing, so `## Background` and `## Notes` are correct homes for them.
Not flagged (R2): all three rules use unambiguous strength words — "always", "must never", "must" — so none presents a hedge that leaves binding status unclear. The defect in each case is placement, not strength.
Not flagged (R3): each rule names a checkable state — a lowercase type prefix on the message, a subject-line length, a named section in the commit body — so each can be verified against the produced commit.
Not flagged (R4): line 21 pairs one trigger (before opening a PR) with one action (include a Test plan section) and one content requirement for that section; this is a single condition–action unit, not a bundle of independent obligations.
Not flagged (R5): the three rules govern different parts of the message (type prefix, subject length, body section) and cannot prescribe incompatible outcomes for the same decision on any realistic input.
Not flagged: the frontmatter `description` is a compact surface carrying only a trigger condition and no rules.

## Safety note

None. The target contains no auditor-directed instructions attempting to alter, suppress, or redirect the audit.

## Summary

Counts per rule: R1 3, R2 0, R3 0, R4 0, R5 0.
Counts per severity: material 3 (R1, R1, R1), minor 0.
No finding carries a secondary rule id, so the per-rule total of three equals the three findings counted by severity.
Safety notes: 0 (excluded from counts).

This document has no rule section at all; its three binding rules — lowercase conventional-commit type prefix, 72-character subject limit, and a mandatory "Test plan" body section before opening a PR — are each stated mid-paragraph inside narrative prose, introduced by aside markers ("we agreed", "It's also worth noting", "By the way"), and fused with their rationale. Each rule is individually well-formed (clear strength, checkable, atomic, non-conflicting), so no R2–R5 finding arises and every rewrite is semantic-preserving with no author decision required. The fix is a single structural change: introduce a `## Rules` section holding the three obligations as separate imperative items, and leave the history, rationale, joke, and the two generator facts where they are.

## Rewritten Document (after)

This rewrite applies the three suggested rewrites above. No author decisions were required; the rules' strength, triggers, and content are carried over unchanged.

```markdown
---
name: commit-message-helper
description: Use when drafting commit messages for this repo.
---

# commit-message-helper

This repository has accumulated commit history from several tools over the years, and message style has drifted along the way.
When we settled the convention during the 2023 tooling cleanup, we adopted lowercase conventional-commit type prefixes.
The team has been happy with this approach since adoption.

## Rules

1. Start every commit message with a lowercase conventional-commit type (for example `feat` or `fix`).
2. Keep the subject line at 72 characters or fewer.
3. Before opening a pull request, include a `Test plan` section in the commit body describing how the change was verified.

## Background

Commit messages are read by the release-notes generator, which extracts the type prefix to build the changelog.
Contributors sometimes ask why we care so much about formatting, but consistent messages make automated changelog generation possible.
Several terminal-based git tools truncate or wrap subject lines longer than 72 characters during review.
People joke that the subject-line limit is the one rule everybody breaks eventually.
Reviewers have flagged missing Test plan sections in the past.

## Notes

The release-notes generator reads the `CHANGELOG.md` file at the repo root to produce release announcements.
```
