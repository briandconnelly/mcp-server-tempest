# Design Workflow

Use this workflow when creating a new documentation surface, redesigning an existing one, or bringing an under-documented repo up to standard for agents to navigate.

## 1. Inventory

List the tracked docs that can change what an agent does on a task.

- Instruction files, wherever the harness in use looks for them.
- README and any docs/ directory content.
- Contribution, testing, and release guides.
- ADRs and other decision-history material.
- Per-directory context files, if the repo uses that pattern.
- Doc-comments and docstrings that carry repo-wide claims, not just code-adjacent ones.

Record what you excluded and why: vendored trees, generated internals, dependency docs, and code comments that carry only file-local constraints.
An inventory with no stated boundary reads as complete when it is not.
Walk the repo tree rather than trusting memory or a stale index.
A doc that isn't in the inventory can't be assigned a layer, linked from an entry point, or checked for staleness later.

## 2. Assign Layers

Give each inventoried doc one primary layer: instruction, orientation, reference, decision history, or code-adjacent context.
Layer definitions live in SKILL.md Vocabulary; this stage only places docs, it doesn't redefine the layers.

- A doc that reads as two layers at once — most often an instruction file carrying reference-depth material — gets its straddling section named here, and split only against the tests in docs-checklist.md Layer Placement.
- Reference-depth material found in the instruction layer is a Token Economy problem: flag it now, move it behind a pointer when you consolidate authority.
- A repo-wide claim sitting only in a code comment is a Comment-Vs-Doc Placement problem: give the fact a doc-level authoritative home and reduce the comment to a pointer to that doc, or to a narrowly code-local note — not a retained repo-wide copy.

Record every straddling or misplaced doc as you go; later stages resolve the split, this stage only finds it.

## 3. Define Read Paths

For the repo's three to five most common tasks, write the ordered list of docs an agent should load to complete each one.

Derive the task list from the repo rather than assuming it: CI job names, Makefile or justfile targets, the section headings in a contribution guide, and the titles of recent pull requests.
Where none of those sources gives a task list, state the three tasks you assumed and mark them as an assumption the repo owner should confirm.

- Name each read path explicitly; "the agent will find it" is not a read path.
- Wire every entry point (README, instruction file) to link to the first doc in each read path.
- Confirm every doc in a read path is reachable by following links, not by knowing its location in advance.

This stage produces Discoverability And Read Path and Task-To-Doc Routing: an entry point that names or links to the read path for each common task, and no orphaned docs.

## 4. Consolidate Authority

For each in-scope claim (see docs-checklist.md Authority And Precedence) that appears in more than one doc, pick one authoritative home and replace every other copy with a link to it.

Find the copies rather than recalling them: search the doc set for the distinctive strings that carry claims — command names, version numbers, thresholds, directory paths — instead of comparing docs sentence by sentence.
State the scope you searched; mark docs you did not search `not-checked` with the reason.

- Where two docs could plausibly conflict despite consolidation, record a stated precedence order that resolves which one wins.
- Decision history is never itself the authoritative home for current policy: if an ADR's content is still binding, promote it into a current-policy doc and link the ADR forward to that doc.

This stage produces Authority And Precedence.

## 5. Set Maintenance Mechanisms

Freshness is a mechanism, not a claim, so give each doc one.

Apply the checks in docs-checklist.md Freshness Mechanisms, Generated-Doc Provenance, and ADR Status And Supersession, and record the mechanism you chose for each doc.
This stage adds no rules of its own; read them from the checklist so that a later change to the standard reaches this stage as well.

Pick mechanisms that someone or something enforces.
A mechanism nobody runs and no gate checks is a claim wearing a mechanism's clothes.

## 6. Checklist Walk

Walk every section of docs-checklist.md against the structure you designed: Layer Placement, Discoverability And Read Path, Task-To-Doc Routing, Authority And Precedence, Canonical Claim Validation, Token Economy, Freshness Mechanisms, Runnable Examples And Commands, Comment-Vs-Doc Placement, Generated-Doc Provenance, and ADR Status And Supersession.

Design Done Criteria: every section is answered in the produced structure, or is explicitly marked not applicable with a one-line justification.
A section with no answer and no justification is unfinished work, not a pass.

Two sections deserve a fresh look here even where earlier stages already touched them: Token Economy and Runnable Examples And Commands.
Re-run their checks from docs-checklist.md against the finished structure rather than trusting earlier-stage answers; a design pass tends to accumulate exactly the convenience additions and unstated preconditions those two sections check for.

## Delegate, Don't Restate

- Instruction-file strategy — canonical instruction file choice, per-harness adapter mechanics — routes to agent-friendly-github.
- Content audits of instruction-layer prose — whether a given sentence binds behavior or merely informs it — route to separating-context-from-constraints.

Apply those skills' answers directly; this workflow does not re-derive them.
