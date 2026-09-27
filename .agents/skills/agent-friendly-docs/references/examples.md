# Examples

Worked shapes for a fictional small repo, `lighthouse` (a billing service), and a fictional monorepo, `orbit` (an API package plus a web package).
Use these as concrete shapes to mimic; cross-reference [docs-checklist.md](docs-checklist.md) for the rules they instantiate and [SKILL.md](../SKILL.md) Vocabulary for the layer names used in the annotations below.

## 1. Layered small-repo layout

`lighthouse` is small enough to fit every layer in one tree.
Each entry below is annotated with the layer it belongs to, per SKILL.md Vocabulary.

```
lighthouse/
├── AGENTS.md                    # instruction layer — canonical, always loaded
├── CLAUDE.md                    # instruction layer — per-harness adapter, points at AGENTS.md
├── README.md                    # orientation layer — entry point and map
├── docs/
│   ├── architecture.md          # orientation layer — system map, read when orienting
│   ├── api-reference.md         # reference layer — loaded only when a task touches the API
│   └── testing.md               # reference layer — loaded only when running or writing tests
├── adr/
│   ├── 0001-use-postgres.md               # decision history — why, not current policy
│   ├── 0002-async-job-queue.md            # decision history — superseded by 0003 (see section 4)
│   └── 0003-replace-rabbitmq-with-kafka.md # decision history — supersedes 0002
└── src/
    └── billing/
        └── invoice.py           # code-adjacent context — comments here carry constraints coupled to this file, not repo-wide claims
```

Two things this layout makes visible at a glance:

- Nothing in `docs/` is always-loaded; an agent reaches `api-reference.md` or `testing.md` only by following a link from `README.md` or `AGENTS.md` when the task calls for it.
- `adr/` sits outside both the instruction and orientation layers; an agent that finds an ADR by search rather than by link reads its status line first, and does not treat its decision as current policy (see section 4 below).

## 2. Monorepo layout with nested context files

`orbit` has two packages with different toolchains, so the instruction layer splits: a root file for cross-cutting norms and a nested file per package for what differs.

```
orbit/
├── AGENTS.md                     # instruction layer — root: cross-cutting norms only (commit format, PR conventions, shared CI gate)
├── CLAUDE.md                     # instruction layer — root adapter, points at AGENTS.md
├── README.md                     # orientation layer — root map, links to each package's README
├── docs/
│   └── architecture.md           # orientation layer — cross-package system map, root only
├── packages/
│   ├── api/
│   │   ├── AGENTS.md             # instruction layer — package-scoped: Go toolchain, `go test ./...`, owns packages/api/
│   │   ├── README.md             # orientation layer — package map
│   │   └── ...
│   └── web/
│       ├── AGENTS.md             # instruction layer — package-scoped: pnpm toolchain, `pnpm test`, owns packages/web/
│       ├── README.md             # orientation layer — package map
│       └── ...
```

What belongs at which level: cross-cutting norms (commit format, review expectations, the label taxonomy) live only in the root `AGENTS.md`; anything that differs by package — build command, test command, ownership, off-limits paths — lives in that package's nested `AGENTS.md` and overrides the root only where it differs.
An agent working in `packages/api/` reads both files: the root file for what's always true, the nested file for what's true here.

This example shows the resulting shape only.
The strategy question — why nest per-package instruction files at all, and how the `CLAUDE.md` adapter mechanics work — is owned by the agent-friendly-github skill's Agent-Instruction-File Strategy section; this skill does not restate those rules.

## 3. README de-bloat before/after

`lighthouse`'s `README.md` started as the only doc anyone wrote, so it accumulated reference-layer weight: a full endpoint-by-endpoint API reference sitting inside an orientation-layer doc.

**Before** (excerpt — the full file ran to roughly 2,400 words, most of it API detail):

````markdown
# lighthouse

A billing service.

## Setup

...

## API

### GET /invoices

Returns a paginated list of invoices. Query params: `status`, `cursor`, `limit`.

Response:
```json
{"items": [...], "next_cursor": "...", "has_more": true}
```

### POST /invoices

Creates an invoice. Body: `{"customer_id": "...", "line_items": [...]}`.

Response:
```json
{"id": "inv_123", "status": "draft", ...}
```

### PATCH /invoices/:id

... (12 more endpoints follow, each with request/response bodies)
````

**After** — the API detail moves to `docs/api-reference.md`; `README.md` keeps only what every task needs to orient, plus a pointer:

```markdown
# lighthouse

A billing service.

## Setup

...

## API

Full endpoint reference: [docs/api-reference.md](docs/api-reference.md).
Load it only when a task touches the API surface directly.
```

Token-cost rationale: before the split, `README.md` was loaded on every orientation pass at roughly 2,400 words, even for tasks — fixing a typo, updating a test — that never touch the API.
After the split, `README.md` is roughly 400 words; the 2,000 words of endpoint detail sit behind an explicit link in `docs/api-reference.md`, loaded only when a task actually needs it.
The fact didn't move to a worse home — it moved to the layer that matches how often an agent actually needs it.

## 4. ADR header with status and supersession

`lighthouse` chose RabbitMQ for its async job queue in ADR 0002, then replaced it with Kafka in ADR 0003.
Both headers carry a `Status` line an agent can read before the surrounding prose.

`adr/0002-async-job-queue.md`:

```markdown
# ADR 0002: Use RabbitMQ for the async job queue

Status: Superseded by [ADR 0003](0003-replace-rabbitmq-with-kafka.md)

## Context

...
```

`adr/0003-replace-rabbitmq-with-kafka.md`:

```markdown
# ADR 0003: Replace RabbitMQ with Kafka for the async job queue

Status: Accepted
Supersedes: [ADR 0002](0002-async-job-queue.md)

## Context

...
```

How an agent should read this: on opening `0002-async-job-queue.md`, the `Status` line is the first fact after the title, before any context or rationale prose.
`Superseded by` means the decision in this ADR is historical, not current policy.
The agent follows the forward link to `0003-replace-rabbitmq-with-kafka.md` to find which decision replaced it.
`Status: Accepted` on 0003 tells the agent that this ADR is the current record of the decision — it does not by itself make the ADR current policy.
Per SKILL.md Vocabulary, an ADR binds only after its content is promoted into a current-policy doc, so the agent reads `docs/architecture.md` for the policy and uses 0003 only for the reason behind it.
If no current-policy doc states the Kafka choice, that is a finding: the decision was never promoted, and every agent must re-derive current policy from decision history.
If a current-policy doc still describes RabbitMQ, that is also a finding — the promotion never happened when the decision changed.

## 5. PR doc-update convention

Freshness in `lighthouse` uses two mechanisms: a PR template line that prompts the doc update, and a CODEOWNERS line that routes doc changes to a reviewer.

`.github/pull_request_template.md` (excerpt):

```markdown
## Checklist

- [ ] Updated the doc that describes this behavior (README, `docs/`, or the relevant `AGENTS.md`), or marked N/A with a one-line reason.
- [ ] Tests pass locally (`pytest`).
```

`CODEOWNERS` (excerpt):

```
docs/       @lighthouse-org/docs-owners
AGENTS.md   @lighthouse-org/docs-owners
adr/        @lighthouse-org/docs-owners
```

The checklist line makes the expectation visible on every PR, but the line does not enforce the update.
CODEOWNERS requests a review only for the paths a PR changes, so these doc-path rules do nothing on a PR that changes behavior in `src/` and touches no doc.
The doc-path rules catch a bad edit to a doc; they do not catch a missing one.
Adding the source paths to CODEOWNERS does not enforce the update either, because a code owner can approve a source-only PR that changes no doc.
Source-path ownership buys routing, not enforcement: the PR reaches a reviewer who is accountable for the doc and can ask for the update.
Only a required check that tests for the doc change can fail the PR, and that check is the difference between a prompt and a gate.
Ownership rules and required checks are owned by agent-friendly-github; this example only states which mechanism catches which failure.

## 6. Harness adapters

Adapter mechanics — which file each harness reads, the include or reference syntax it supports, and what to do when it supports none — are owned by the agent-friendly-github skill's Agent-Instruction-File Strategy section.
Apply that skill directly; this skill states no harness-specific syntax anywhere, because a copy here would age out of step with the authoritative rule and nothing would fail when it did.
For doc-surface design, the only fact this skill needs is the shape shown in sections 1 and 2: one canonical instruction file, with per-harness files as adapters that point at it.
