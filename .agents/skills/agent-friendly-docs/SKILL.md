---
description: Use when designing, structuring, auditing, or reviewing the documentation surface of a repository that AI coding agents read while working — instruction files, README, docs/, ADRs, per-directory context files, and code-adjacent comments. Symptoms include agents re-deriving project context every session, reading stale or wrong docs, instruction files bloated with reference material, README token bloat, ADRs mistaken for current policy, embedded commands that fail as written, duplicated content drifting apart, and repo-wide context trapped in code comments. Covers layering and placement, discoverability and read paths, one authoritative home per fact, token economy, freshness mechanisms, and runnable examples. Not for published docs sites or llms.txt, generic prose quality, GitHub repo safety configuration, or rules-vs-context audits of instruction-file content.
metadata:
    github-path: agent-friendly-docs
    github-ref: refs/heads/main
    github-repo: https://github.com/briandconnelly/skills
    github-tree-sha: 35c35612e30726706c16f5ac4cbaaee0d36092cb
name: agent-friendly-docs
---
# Agent-Friendly Docs

Use this skill to make a repo's documentation surface cheap for agents to navigate and trust.

## Core Standard

The checks that decide a pass or a finding live in [docs-checklist.md](references/docs-checklist.md), one per section.
This list names what each section is about so you can pick one; it is a map, not a second copy of the rules.
Read the section before you apply it, and where this list and the checklist read differently, the checklist wins.

- **Layer Placement** — which layer each doc belongs to, and when a straddling section is split out.
- **Discoverability And Read Path**, **Task-To-Doc Routing** — whether an agent reaches the right doc by following links, per task.
- **Authority And Precedence** — one home per claim that could diverge, and what resolves a conflict.
- **Canonical Claim Validation** — whether the authoritative doc is true, checked against the code rather than against another doc.
- **Token Economy** — what earns a place in the always-loaded layer.
- **Freshness Mechanisms**, **Generated-Doc Provenance**, **ADR Status And Supersession** — what keeps a doc correct, marks a generated one, and separates a live decision from a superseded one.
- **Runnable Examples And Commands** — whether an embedded command runs as written.
- **Comment-Vs-Doc Placement** — which constraints travel with the code and which need a doc.

## When To Use

- Designing or restructuring a repo's documentation surface.
- Auditing an existing documentation surface for agent-friendliness.
- Diagnosing a concrete agent failure: missing project conventions, reading stale docs, re-deriving context every session.

## When Not To Use

- Published documentation sites or llms.txt — this skill covers repo-internal docs only.
- Generic prose quality or writing style with no agent-consumption angle.
- Instruction-file strategy and repo safety configuration — use agent-friendly-github.
- Rules-vs-context content audits of instruction-file prose — use separating-context-from-constraints.
- Trivial edits to a doc surface that is already well-layered; just make the edit.

## Vocabulary

- **Instruction layer** — always-loaded binding norms: the canonical instruction file plus thin per-harness adapters.
  Adapter strategy itself is owned by agent-friendly-github, not this skill.
- **Orientation layer** — read-on-demand maps: README, architecture overviews, CONTEXT.md, per-directory context files.
  Loaded when an agent orients itself, not on every turn.
- **Reference layer** — detailed how-to and API material, loaded only when a task demands it.
  Kept out of the instruction layer precisely because it is heavy.
- **Decision history** — ADRs and postmortems that explain why a past choice was made.
  Never binds unless promoted into a current-policy doc.
- **Code-adjacent context** — comments and docstrings carrying constraints that must travel with the code.
  Repo-wide context does not belong here even when it is convenient to write.
- **Canonical instruction file** — the one instruction file a harness reads directly.
  Other harnesses point at it through a thin adapter instead of duplicating it.
- **Per-harness adapter** — a thin, harness-specific file that points at the canonical instruction file instead of restating it.
- **Read path** — the sequence of docs an agent loads, in order, to complete a given task.
- **Authoritative vs historical** — whether a doc states current policy or merely records a past decision.
- **Generated-doc provenance** — a marker on a generated file naming its source and regeneration command.
- These layers are a routing lens for "what does an agent read first, what is authoritative, what is historical, what is ignorable" — not a filing system every repo must adopt.

## Workflow

1. Identify the audience: repo owner, who can restructure, versus contributor or agent operator, who works within what exists.
   Audience decides what to lead with.
   Where the user does not say and the repo gives no ownership signal, assume the repo owner, state that assumption, and mark each owner-only remediation as such.
2. Classify the task: design/restructure, audit of an existing surface, or diagnosis of a concrete failure.
3. For design or restructure, follow [design-workflow.md](references/design-workflow.md); for audit or diagnosis, follow [review-workflow.md](references/review-workflow.md).
4. Design tasks and audits walk [docs-checklist.md](references/docs-checklist.md) as the shared standard; a diagnosis names only the sections its failure touches and produces no coverage table.
5. Delegate instruction-file strategy questions to agent-friendly-github.
   Delegate rules-vs-context content audits of instruction-layer docs to separating-context-from-constraints.
   That skill counts as available when it is loaded in the current session.
   When it is not loaded, apply one screening question — does this sentence bind behavior or just inform it? — label the result provisional, and recommend a full audit with that skill.
6. Use [examples.md](references/examples.md) for concrete shapes.

## Done Criteria

Before declaring done, read the relevant workflow, then apply the criteria for your task type below.
Only design tasks and audits walk [docs-checklist.md](references/docs-checklist.md) section by section.

- **Design tasks**: every checklist section is answered in the produced structure or explicitly marked not-applicable with a one-line justification.
- **Review tasks**: every checklist section is covered by a finding, marked OK with brief evidence, or noted not-checked with reason.
- **Diagnosis tasks**: the response names the most likely failure path, leads with the immediate mitigation, and separates it from owner-side restructuring.
  No checklist walk and no coverage table — naming the one or two sections the failure falls under is the whole of the checklist's role here.
