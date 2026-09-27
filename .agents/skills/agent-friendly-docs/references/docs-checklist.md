# Docs Checklist

Use this as the detailed standard for both design and review tasks.

## Layer Placement

- Every doc is assigned exactly one primary layer: instruction, orientation, reference, decision history, or code-adjacent context.
- Every section whose loading cost, authority, or lifecycle differs from its doc's primary layer is named.
- A named section is split out only when the audit can state the evidence for one of three tests.
  Loading: name a task on the repo's common-task list that loads the doc and never needs that section.
  Authority: name a second doc that states the same claim, so which one governs is open.
  Lifecycle: name a distinct owner, generator, or change trigger for the section.
- A section that meets none of the three tests stays where it is.
  A short quick-start command inside an orientation README meets none of them.
- The instruction layer carries binding norms and pointers only, not reference-depth material.
- Decision history is labeled historical, not current policy.

Layer names and definitions live in SKILL.md Vocabulary; this section only checks that every doc has been placed in one of them.
A doc that straddles two layers is a signal to name the straddling section, then to split it only when one of the three tests above is met.
Splitting on sight fragments a usable doc into many small ones and raises navigation cost.
Whether a given sentence in the instruction layer is a binding norm or merely informative context is a separating-context-from-constraints question, not one this checklist re-derives; see SKILL.md Workflow for when to apply that skill and what to do when it is not loaded.
Canonical-instruction-file and per-harness-adapter strategy is owned by agent-friendly-github; this section checks placement only, not adapter mechanics.

## Discoverability And Read Path

- Every instruction, orientation, reference, and decision-history doc is reachable by links from at least one entry point (README or an instruction file).
- An agent orienting itself can reach the doc that answers a given question by following links, without reading unrelated docs first.
- No doc in those layers is orphaned: reachable only by knowing its path in advance.
- Code-adjacent comments and generated internals are exempt from the link requirement, and the audit states that exemption rather than reporting them as orphans.

Entry points carry the map; a doc that no entry point links to is found only by search, and an agent that does not know it exists does not search for it.

## Task-To-Doc Routing

- Each of the repo's common tasks (add a feature, fix a bug, run tests, cut a release) has an identifiable read path: a named sequence of docs to load.
- The entry point names that read path, or names where to find it, for each common task.
- A read path can be completed by following links; it does not require guessing which file is relevant.

This is Discoverability And Read Path applied to specific, recurring tasks rather than to an arbitrary question.

## Authority And Precedence

- Every normative or operational claim has exactly one authoritative home.
  A claim is in scope when two copies of it could diverge and change what an agent does: commands, versions, thresholds, paths, ownership, conventions, policy statements, and current-state descriptions of architecture or deployment.
  Out of scope: names, quotations, historical statements, and explanatory background that cannot change an action.
  Prose role does not decide this — a current-state fact written as background is in scope, because an agent implements against it.
- Every other mention of an in-scope claim is a link to the authoritative home, not a restatement.
- Every generated mirror or quotation of an in-scope claim is marked as non-authoritative, so it is not read as a second home.
- Where two docs stating in-scope claims can conflict, a stated precedence order resolves which one wins.

Duplication is the symptom; the fix is a link, not a rewrite in both places.

## Canonical Claim Validation

- Every command, version, path, and current-state claim in an authoritative doc is checked against the source that implements it: the code, CI configuration, build files, manifests, or schema.
- No claim is marked `OK` because no other doc contradicts it.
- Every claim that cannot be checked against a source is marked `not-checked` with the reason.
- Where the repo is too large to check every claim, the sampling boundary is stated.

Authority And Precedence finds two docs that disagree; it cannot find one doc that is uniformly wrong.
A single stale command with no competitor passes every other section in this checklist, and an agent runs it with full confidence.

## Token Economy

- Every procedure or reference statement in the instruction layer applies to every task in the repo's common-task list.
  A procedure that fewer tasks need moves behind a pointer, and the pointer stays.
- A routing pointer is exempt from the rule above: a one-line pointer that names a task and the doc it routes to belongs in the instruction layer even when only one task needs it.
  Pointers are what make the layer small; the rule removes procedures, not routes.
- The instruction layer carries pointers, not procedures, for anything an agent can complete a common task without.
- No bulk content is duplicated across layers (e.g., reference material copied into the instruction file for convenience).
- Every orientation-layer doc that carries reference or historical material — full API detail, changelogs — moves that material behind a pointer to its own layer.

Every always-loaded token is a token spent on every single turn; the instruction layer's size is a standing cost, not a one-time one.

## Freshness Mechanisms

- Each doc (or the section of the repo it covers) has a named owner or owning team.
- PRs that change behavior a doc describes carry a stated expectation to update that doc.
- No doc claims freshness by timestamp or "last updated" date alone, without a mechanism that keeps it true.

A timestamp records when a doc was last touched, not whether it is still correct; ownership and PR expectations are what keep it correct.

## Runnable Examples And Commands

- Every embedded command runs as written from the repo root, or the doc states the precondition needed to run it (working directory, environment variable, prior setup step).
- Every path referenced in an example resolves from the stated starting point.
- No example depends on unstated state (an unmentioned file, an unmentioned prior command) to succeed.

An agent will copy-paste the example as written; if it doesn't run, the doc has failed at its one job.

## Comment-Vs-Doc Placement

- Constraints coupled to a specific piece of code (why this line is guarded, why this default was chosen) live in a comment or docstring next to that code.
- Repo-wide context (architecture, conventions, cross-cutting policy) never hides in a code comment where only a reader of that one file will see it.
- Where a comment states a repo-wide fact, that fact also has an authoritative home in a doc, per Authority And Precedence.

Code-adjacent context travels with the code by design; repo-wide context needs to be found without first finding the code.

## Generated-Doc Provenance

- Every generated doc is marked as generated.
- Every generated doc names its source (the file, script, or tool that produces it).
- Every generated doc gives the regeneration command.

An agent that doesn't know a doc is generated will edit it directly and lose the edit on the next regeneration.

## ADR Status And Supersession

- Every ADR carries a status (e.g., proposed, accepted, superseded, rejected).
- Every superseded ADR links forward to the ADR or doc that superseded it.
- No ADR is treated as binding current policy unless its content has been promoted into a current-policy doc; ADRs are decision history by default, per SKILL.md Vocabulary.

Status and forward links are what let an agent tell a decision that is in force from a superseded decision, without reading the whole history.
