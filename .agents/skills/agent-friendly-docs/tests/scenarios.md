# Test Scenarios for agent-friendly-docs

Behavioral test scenarios for this skill, following the baseline/with-skill methodology: run each scenario with a fresh subagent that does NOT have the skill loaded (baseline), then with the skill loaded (treatment), and compare against the assertions.
A baseline run that already satisfies every assertion means the scenario is too easy; tighten it.
An assertion the with-skill run misses is a finding against the skill, not against the agent.

## How to run

1. **Baseline:** dispatch a subagent with only the scenario prompt below.
   Record which assertions its output satisfies.
2. **Treatment:** dispatch a fresh subagent with the skill content available (or triggered via its description) and the same prompt.
   Load agent-friendly-docs only.
   Sibling skills are named in its text but are not loaded, so a scenario that tests delegation expects the treatment run to route by name and to decline the delegated work, not to apply the sibling's rules.
3. **Score:** every assertion is pass/fail with a one-line evidence pointer into the transcript.
   Record results in the table at the bottom.
   Assertion lists may be tightened over time; a results row reflects the assertions as of its date.

**Scoring rule.**
A scenario passes when the treatment run satisfies every assertion.
A scenario is valid as a *discrimination* test only when the baseline run fails at least one assertion that is about analysis rather than format — a missed finding, a wrong severity, an unfounded certainty.
A baseline that fails only on format (no coverage table, no evidence labels) does not establish that the skill improves judgment; tighten that scenario before its treatment result counts as evidence of benefit.

One exception, which must be labeled: a scenario the baseline passes fully is still worth keeping as a **regression test** when the treatment can score below the baseline.
Scenario 3 is such a case — it is not evidence that the skill helps, and it is not scored that way; it is evidence that the skill does no harm.
Mark every scenario as `discrimination` or `regression` so no reader mistakes one for the other.

Record baseline and treatment per assertion, not per scenario, so a regression can be traced to the assertion it broke.

## Scenario 1: Design (application test) — `discrimination`

**Prompt:**

> Structure the documentation surface for `fleetlog`, a mid-size vehicle-telemetry service.
> Today every doc lives as a flat pile of markdown at the repo root, with no folders and no stated reading order:
>
> ```text
> fleetlog/
> ├── README.md              — 30-line project blurb plus a wall of setup steps
> ├── CLAUDE.md               — build/lint/test commands, a few "always/never" rules
> ├── copilot-instructions.md — same build/lint/test commands, copy-pasted from CLAUDE.md
> ├── CONTRIBUTING.md         — PR process, commit style, review expectations
> ├── ARCHITECTURE.md         — service boundaries, data flow, current storage choice
> ├── TESTING.md              — how to run unit and integration tests, fixture layout
> ├── DEPLOY.md               — how to cut and ship a release
> ├── STYLE.md                — naming and formatting conventions
> ├── ADR-001-database.md     — why Postgres was chosen (no status field)
> ├── ADR-002-queue.md        — the original queue choice, later abandoned (no status field)
> └── API.md                  — full REST endpoint reference
> ```
>
> The repo's most common tasks are: add a feature, fix a bug, run the tests, and cut a release.
> Produce the restructured documentation surface: where each existing doc lives afterward, what (if anything) merges or splits, the read path for each of the four named tasks, and how each doc stays correct over time.

**Assertions (with-skill run must satisfy):**

- [ ] Every listed doc is given one primary layer — instruction, orientation, reference, or decision history — with `CLAUDE.md`/`copilot-instructions.md` in the instruction layer and `ADR-001`/`ADR-002` in decision history (Layer Placement).
- [ ] The build/lint/test commands duplicated between `CLAUDE.md` and `copilot-instructions.md` are flagged as an authority problem: exactly one authoritative home is named and the duplicate is reduced to a reference rather than a second copy, with the choice of adapter shape routed to agent-friendly-github rather than restated (Layer Placement, Authority And Precedence).
- [ ] A named, ordered read path is produced for each of the four tasks — add a feature, fix a bug, run the tests, cut a release — reachable from an entry point rather than left implicit (Task-To-Doc Routing).
- [ ] The database choice and the queue choice each get exactly one authoritative home, with `ADR-001`/`ADR-002` reduced to historical record plus a forward pointer if either decision is still binding (Authority And Precedence, ADR Status And Supersession).
- [ ] `ADR-001` and `ADR-002` are each assigned a status field, and `ADR-002` (superseded by the later queue move) links forward to whatever replaced it (ADR Status And Supersession).
- [ ] `API.md`'s endpoint reference is placed in the reference layer, not folded into `README.md` or `CLAUDE.md` (Token Economy).
- [ ] Every doc gets an owner and a stated PR-update expectation, not a timestamp alone (Freshness Mechanisms).
- [ ] The checklist walk is completed against the new structure, with every docs-checklist.md section answered or marked not-applicable with a one-line reason (Runnable Examples And Commands and Comment-Vs-Doc Placement included even though no example/comment was in the pile).

**Expected baseline failures:** no explicit layer assignment (docs left in a flat list with new folder names but no stated placement rule), `copilot-instructions.md` duplication left standing or merely "kept in sync" rather than turned into a pointer, read paths described in prose without a named per-task sequence, ADRs renamed or moved but given no status field, no owner or PR-update mechanism stated, no checklist walk performed.

## Scenario 2: Audit (retrieval test) — `discrimination`

**Prompt:**

> Audit this repo's documentation surface for agent-friendliness and report your findings.
> You cannot browse the repo or run commands; you have only this captured material.
> The audience is the repo's own maintainers, who can change anything.
>
> File tree:
>
> ```text
> ledgerly/
> ├── README.md
> ├── CLAUDE.md
> ├── .github/copilot-instructions.md
> ├── docs/
> │   ├── adr/0003-postgres-over-dynamo.md
> │   ├── api.md              — canonical REST endpoint reference
> │   └── testing.md
> ├── test/
> │   └── unit/test_reconcile.py
> └── src/ledgerly/reconcile.py
> ```
>
> `README.md` (excerpt, ~120 lines total):
>
> ```markdown
> # ledgerly
>
> Ledgerly is an internal invoicing and reconciliation service.
>
> ## Setup
> ...(12 lines)...
>
> ## Full API Reference
> ### POST /invoices
> ...(38 lines fully duplicating docs/api.md, endpoint by endpoint, with the same request/response examples)...
>
> ## Running Tests
> Run the full suite with `pytest tests/unit -v`.
> ...(9 more lines duplicating docs/testing.md's instructions almost verbatim)...
>
> ## Changelog
> ...(every release back to v0.1, 40 lines)...
> ```
>
> `CLAUDE.md` (canonical instruction file, in full):
>
> ```markdown
> # Instructions
> - Run tests with `uv run pytest --cov=ledgerly test/unit`; coverage must stay at or above 85%.
> - Model all ledger entries per ADR-0003 (Postgres rows) — this is current policy.
> - Never commit generated files under `dist/`.
> ```
>
> `.github/copilot-instructions.md` (in full):
>
> ```markdown
> # Copilot Instructions for ledgerly
> - Run tests with `pytest test/unit`; coverage must stay at or above 95%.
> - Model all ledger entries per ADR-0003 (Postgres rows).
> - Never commit generated files under `dist/`.
> ```
>
> `docs/adr/0003-postgres-over-dynamo.md` (in full):
>
> ```markdown
> # ADR-0003: Postgres over DynamoDB for ledger storage
>
> We will model ledger entries as rows in our existing Postgres instance rather than
> standing up DynamoDB, to avoid operating a second datastore.
> ```
>
> Separately captured context — a note from the platform team, six months after the ADR above was written, in a Slack thread never folded into the ADR file itself:
>
> > "we migrated ledger storage to DynamoDB in v2 for the throughput; this doc is now historical."
>
> `docs/testing.md` (excerpt):
>
> ```markdown
> ## Running the suite
> From the repo root: `pytest tests/unit -v`
> ```
>
> `src/ledgerly/reconcile.py` (top-of-file comment, in full):
>
> ```python
> # Reconciliation policy for the whole ledgerly service:
> # - every mismatch retries 3x with exponential backoff starting at 200ms
> # - a mismatch that survives 3 retries pages the on-call rotation
> # - this applies to every reconciliation job in the service, not just this file
> import ...
> ```
>

**Assertions (with-skill run must satisfy):**

- [ ] `ADR-0003` is flagged `blocking` under ADR Status And Supersession: it carries no status field, is cited by `CLAUDE.md` as current policy, and the service has since moved off Postgres per the buried Slack note — evidence labeled `observed` for the doc text and `inferred` for whether DynamoDB fully replaced the pattern in code.
- [ ] The `CLAUDE.md`/`copilot-instructions.md` divergence (85% vs. 95% coverage, `--cov=ledgerly` flag present vs. dropped) is flagged `blocking` under Authority And Precedence as a contradictory-authority finding, `observed` directly from the two quoted files.
- [ ] The `pytest tests/unit -v` command in both `README.md` and `docs/testing.md` is flagged `blocking` under Runnable Examples And Commands: the tree shows tests live at `test/unit` (singular), not `tests/unit`.
  The path mismatch is labeled `observed` from the tree and the quoted command; the conclusion that the command fails is labeled `inferred`, because this scenario forbids running it.
- [ ] `README.md`'s duplicated API reference, test instructions, and full changelog are flagged `degrading` under Token Economy as bulk reference material carried in the orientation layer instead of pointed to, `observed` from the excerpt.
- [ ] The reconciliation retry/backoff policy embedded only in `reconcile.py`'s header comment is flagged under Comment-Vs-Doc Placement at `degrading`, or at `blocking` with the severity doubt stated as Review Workflow §4 requires: repo-wide policy with no doc-level authoritative home, `observed` from the comment plus `absence-of-evidence` for a corresponding doc.
  The comment no longer states that it is the only home; the agent must check the rest of the captured material to establish that.
- [ ] The absence of any release documentation is noticed unprompted and flagged `degrading` under Task-To-Doc Routing, evidence labeled `absence-of-evidence`.
  The prompt does not state that the gap exists; the agent must find it by walking the common tasks against the tree.
- [ ] A section-by-section coverage table is produced covering all eleven docs-checklist.md sections, with `not-checked` and a reason for any section the captured material cannot answer (e.g., Discoverability And Read Path beyond what the tree shows, Generated-Doc Provenance).
  Canonical Claim Validation is marked `not-checked` for lack of a runnable checkout, not `OK`.
- [ ] Findings are ordered blocking first, then degrading, per Report Format, and each uses the six-part finding format: severity, checklist section, location, evidence labels, impact, remediation.

**Expected baseline failures:** ad-hoc or no severity scale, no distinction between the three blocking findings and the three degrading ones (or all six flattened to one tier), no evidence labels, the adapter drift and the stale-ADR-as-policy finding conflated or missed entirely, the `test/unit` vs. `tests/unit` path mismatch missed because the command "looks fine" without cross-checking the tree, no coverage table.

## Scenario 3: Diagnosis (routing test) — `regression`

**Prompt:**

> Our coding agent keeps missing our test conventions and reviewers keep bouncing the same PRs back for it.
> Our test conventions — table-driven tests, `t.Parallel()` on every subtest, golden files under `testdata/` — live in a "Testing" section partway down `CONTRIBUTING.md`.
> Our `CLAUDE.md` file lists build, lint, and test *commands* but never mentions `CONTRIBUTING.md` or these conventions.
> `README.md` links to `CONTRIBUTING.md` under a "Contributing" heading near the bottom of the file, below installation and deployment instructions.
> What's going on, and what should we do?

**Assertions (with-skill run must satisfy):**

- [ ] Names the most likely failure path: the agent loads `CLAUDE.md` (and possibly the top of `README.md`) but never reaches `CONTRIBUTING.md`'s "Testing" section, so the conventions never enter its context — the doc locations `observed` from the prompt, the "never reaches it" mechanism `inferred`.
- [ ] Leads with a smallest immediate mitigation drawn from Review Workflow §1 — a reminder in the task prompt, or a pointer from `CLAUDE.md`'s test-command entry to `CONTRIBUTING.md`'s Testing section — stated before any restructuring.
  Any of the §1 mitigations passes; leading with the restructuring fails.
- [ ] Does not create a second authoritative home.
  If it proposes moving the conventions into `CLAUDE.md`, it replaces the `CONTRIBUTING.md` text with a pointer in the same change.
  Leaving both copies standing fails, because that is the duplicate authority the skill exists to prevent.
- [ ] Separates that immediate mitigation from owner-side restructuring (e.g., reconsidering why test conventions live inside a contributing-process doc rather than as their own referenced doc) and frames the latter as a follow-up, not a blocker to today's fix.
- [ ] Stays diagnosis-sized: no full checklist coverage table, no audit of unrelated sections (SKILL.md Done Criteria, Diagnosis tasks).

**Expected baseline failures:** jumps straight to "rewrite your docs" without naming why the agent misses the convention today, no evidence-label distinction between what's stated in the prompt and what's deduced about agent behavior, immediate fix and larger restructuring blended into one undifferentiated list, or a full audit-style walk of the whole doc surface for a two-file problem.

## Scenario 4: Boundary (delegation test) — `discrimination`

**Prompt:**

> We're consolidating on a single canonical `CLAUDE.md`, with thin adapter files for Cursor and Copilot that point at it instead of repeating it — tell us how to structure those adapters.
> Separately: `CLAUDE.md` currently has "Keep responses concise" sitting right next to "Never delete a file without explicit confirmation," and we can't tell which of our instruction-file lines are actually supposed to bind the agent's behavior versus which are just style preference — sort that out for us too.

**Assertions (with-skill run must satisfy):**

- [ ] Declines to design the per-harness adapter mechanics itself and routes that question to agent-friendly-github instead of proposing an adapter file format or pointer syntax (SKILL.md Vocabulary, Workflow §5).
- [ ] Declines to adjudicate which `CLAUDE.md` lines bind versus inform and routes that question to separating-context-from-constraints.
  Because treatment loads this skill alone, the sibling is not available, so the run may apply the one screening question ("does this sentence bind behavior or just inform it?"), label the result provisional, and recommend the full audit — it must not work the full distinction itself (Workflow §5).
- [ ] Does not silently answer both delegated questions in full as though they were in scope, and does not refuse the entire prompt outright — it names what it can still speak to directly, such as where the canonical file and its adapters sit in the layer model (Layer Placement) once the mechanics and the binds-vs-informs split are handled elsewhere.
- [ ] Does not restate agent-friendly-github's or separating-context-from-constraints's content from memory as if it were this skill's own material.

**Expected baseline failures:** answers the adapter-format question directly with an invented pointer syntax, sorts the "concise" vs. "never delete" lines into bind/inform buckets itself instead of naming the boundary, no mention of either sibling skill, or the whole prompt waved off as entirely out of scope with nothing addressed.

## Scenario 5: Restraint (negative-trigger test) — `discrimination`

Run each prompt below as its own trial.
The skill's exclusions are part of its contract, so a treatment run that walks the checklist against any of these prompts is a failure, not a thorough answer.

**Prompt 5a:**

> Our public documentation site is built with Docusaurus and goes live next week.
> Read through the getting-started page and tighten the writing — it's wordy and the tone is inconsistent.

**Prompt 5b:**

> Write an `llms.txt` for our project so language models can consume our published docs.

**Prompt 5c:**

> Our `AGENTS.md` is a wall of vague lines — "prefer small commits", "be careful with migrations", "never force-push to main".
> Sort out which of these actually bind the agent and which are just advice.

**Assertions (with-skill run must satisfy):**

- [ ] 5a: treats the request as prose editing for a published docs site, and does not produce a layer assignment, read path, or checklist walk (SKILL.md When Not To Use).
- [ ] 5b: declines `llms.txt` as out of scope, or answers it without invoking this skill's standard; no docs-checklist.md section is walked (SKILL.md When Not To Use).
- [ ] 5c: routes the bind-versus-inform question to separating-context-from-constraints rather than sorting the lines itself; because that skill is not loaded in treatment, it may apply the one screening question, label the result provisional, and recommend the full audit (SKILL.md Workflow §5).
- [ ] None of the three responses produces a severity-labeled finding list against the docs-checklist.md sections.

**Expected failure mode this scenario guards against:** a description broadened to fix a false negative starts firing on human-facing prose reviews and on the sibling skill's core request, and no other scenario would catch it.

## Results

First run: 2026-08-19, on commit 355b641 (all five scenarios, both arms, one repetition each).
Treatment loaded agent-friendly-docs only; baseline was blocked from the skills directory.
Single repetition, one model — treat every row as a signal, not a measurement.
These rows record aggregate scores per scenario, not the per-assertion detail the scoring rule above asks for; the per-assertion record is owed on the next run.
Scenario 3's assertion list was split from four items into five after these runs, so its scores below are against the four-item list of that date.
Scenario 2's comment-placement assertion was also loosened afterward, for the reason given in its row.

| Date | Scenario | Run | Assertions passed | Notes |
| --- | --- | --- | --- | --- |
| 2026-08-19 | 1 Design | baseline | ~5.5/8 | Produced layered tree, one-home fix, four read paths, ADR statuses, owners, PR template. Missed: explicit per-doc layer assignment, delegation of adapter choice, checklist walk. |
| 2026-08-19 | 1 Design | treatment | 8/8 | Named three straddling docs against the split tests, delegated to both siblings, marked Canonical Claim Validation `not-checked`, walked all eleven sections. |
| 2026-08-19 | 2 Audit | baseline | ~4/8 | Found every planted content defect, including the `test/unit` path mismatch as its top finding. Missed: the unprompted release-routing gap, evidence labels, the severity scale, the coverage table. |
| 2026-08-19 | 2 Audit | treatment | 8/8 | Ten findings, six-part format, correct `inferred` label on the unexecuted command, sampling boundary stated under Canonical Claim Validation. |
| 2026-08-19 | 3 Diagnosis | baseline | 4/4 | Named the failure path, led with the pointer fix, kept one authoritative home, stayed diagnosis-sized. |
| 2026-08-19 | 3 Diagnosis | treatment | 2/4 | **Regression — treatment worse than baseline.** Produced six findings and a full eleven-section coverage table for a two-file problem, and buried the immediate mitigation below them. Cause: review-workflow §1 said "start in diagnosis mode" without saying stop, and SKILL.md said *both* workflows walk the checklist. Fixed after this run; re-run owed. |
| 2026-08-19 | 3 Diagnosis | treatment (re-run, b46f098) | 4/4 | **Regression fixed.** No coverage table; names only Task-To-Doc Routing and Discoverability in a few words. Leads with the caller-side prompt fix, then the owner-side steps. Refused the duplicate-authority shortcut unprompted: "does not copy the conventions into CLAUDE.md ... the drift is silent." |
| 2026-08-19 | 4 Boundary | baseline | ~1/4 | Answered both delegated questions in full, including an invented adapter file layout and a complete bind-vs-inform framework. No sibling skill named. |
| 2026-08-19 | 4 Boundary | treatment | 4/4 | Declined adapter mechanics and stated no harness syntax, routed the bind-vs-inform question and labeled its screening result provisional, still answered the layer-placement part. Strongest discrimination in the suite. |
| 2026-08-19 | 5 Restraint | baseline | 3/4 | 5a and 5b answered normally, as intended. Failed 5c: sorted the binding lines itself with its own framework and named no sibling skill. |
| 2026-08-19 | 5 Restraint | treatment | 4/4 | Declined 5a and 5b against When Not To Use after reading SKILL.md alone, routed 5c, walked no checklist section. |

**What this run says about the scenarios themselves.**

- Scenario 4 and Scenario 5 discriminate well: the baseline fails them on analysis, not on formatting.
- Scenario 2 now discriminates on analysis too — removing the self-announcing hints made the release-routing gap a real find, and the baseline missed it.
- Scenario 1 is the weakest.
  The baseline found every content answer and failed mainly on layer vocabulary and the checklist walk, which is close to a format-only failure.
  Tighten it before its treatment result carries weight — plant a defect that needs the standard to see, such as a command that contradicts a CI file.
- Scenario 3 is labeled `regression`, not `discrimination`.
  The baseline passes it fully, so it is not evidence that the skill helps; it caught the skill actively doing harm, which is what a regression test is for.
  The re-run after the fix passed, so keep it as a standing guard against audit creep.
