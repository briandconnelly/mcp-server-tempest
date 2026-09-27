# Review Workflow

Use this workflow when auditing an existing documentation surface or diagnosing a concrete agent failure.

## 1. Route Audit Vs Diagnosis

If the user reports a concrete failure — an agent missed a convention, read a stale doc, or re-derived context it should have found — start in diagnosis mode.

Diagnosis mode is the whole workflow for that request, not its first stage.
Produce these four things and stop:

- name the most likely failure path: which doc the agent should have read, and why it didn't
- lead with the smallest caller-side mitigation that unblocks the agent today (a pointer, a link, a reminder in the task prompt), stated before any restructuring
- separate that from the owner-side restructuring that fixes the surface itself
- if confirming the hypothesis needs reading a doc the caller hasn't shared, ask before assuming its contents

In diagnosis mode, do not walk the checklist, do not produce a coverage table, and do not open sections the reported failure does not touch.
Sections 2 to 6 below are for audits only.
A diagnosis answered with a full section-by-section audit buries the one fix the user needs today, and charges them for ten sections of a surface they did not ask about.
Use the checklist only to name which section the failure falls under, in a few words.

Only when the user asks for a general audit of the documentation surface, continue with the full workflow below.

## 2. Establish Evidence

Prefer direct evidence over inferred behavior.

Label each piece of evidence within a finding as one of:

- `observed` — you read the doc, followed the link, or ran the command yourself
- `inferred` — deduced from related material without reading the doc directly
- `absence-of-evidence` — a required piece is missing: no read path for a core task, no owner named, no regeneration command on a generated doc

Absence of a required piece is itself a finding, not a gap to note and move past.

Read the repo's actual doc tree rather than trusting an index or a prior summary of it; a doc that moved or was deleted since the index was written produces a false `OK`.

Two checks are never satisfied by reading alone:

- **Runnable Examples And Commands.** Run each embedded command from the working directory the doc states, in a checkout you can execute.
  Where you cannot execute, resolve every path, file, and directory the command names against the repo tree, and label the result `inferred` with the unresolved parts named.
  Never mark this section `OK` from a command that only looks correct.
- **Canonical Claim Validation.** Check the claim against the source that implements it, not against another doc.

A command that reads as plausible and a command that runs are different findings; only one of them is evidence.

## 3. Walk The Checklist

Walk every section of [docs-checklist.md](docs-checklist.md) in order: Layer Placement, Discoverability And Read Path, Task-To-Doc Routing, Authority And Precedence, Canonical Claim Validation, Token Economy, Freshness Mechanisms, Runnable Examples And Commands, Comment-Vs-Doc Placement, Generated-Doc Provenance, and ADR Status And Supersession.

For each section, produce at least one of:

- a finding (see Finding Format below)
- `OK` with the brief evidence that grounds it (the doc, link, or command you checked)
- `not-checked` with the reason (out of scope, no access, not applicable to this repo)

A section with no finding, no `OK`, and no `not-checked` reason is unfinished work, not a pass.
Cite the checklist's own checks by section name rather than restating them; this workflow does not re-derive what docs-checklist.md already defines.

## 4. Severity Scale

Assign severity by what the finding changes, and decide it in this order:

- `blocking` — the evidence shows an agent can produce a wrong result: it edits the wrong file, runs a command that fails or does the wrong thing, or follows a superseded decision as current policy.
  Authority conflicts between two docs belong here.
- `degrading` — the agent still reaches the correct result, but pays an avoidable cost to get there: token bloat in the instruction layer, a missing read path that forces rediscovery, context buried where the agent finds it late.
- `polish` — neither cost is demonstrable from the evidence you hold: inconsistent terminology, a link that could be one hop shorter, formatting noise.

Apply the first tier whose test the evidence satisfies.
Where the evidence supports two tiers, assign the higher one and state the doubt in the impact line.
Never lower a severity because the fix is large; effort belongs in remediation, not in severity.

## 5. Finding Format

Each finding includes:

- severity: `blocking`, `degrading`, or `polish`
- checklist section: the docs-checklist.md section it violates
- location: file and section cited
- evidence labels: one per evidence item — `observed`, `inferred`, or `absence-of-evidence`
- impact: one line, stated in terms of what an agent does wrong or pays for
- remediation: the smallest fix first, with a larger restructuring noted separately if one is warranted

## 6. Report Format

Order the report as:

1. Findings, ordered by severity (`blocking` first, then `degrading`, then `polish`).
2. The section-by-section coverage table produced in Walk The Checklist: every docs-checklist.md section marked with a finding reference, `OK`, or `not-checked`.

When no findings surface, state that explicitly and name any section left `not-checked` and why.
