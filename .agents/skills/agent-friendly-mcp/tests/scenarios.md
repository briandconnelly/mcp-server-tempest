# Test Scenarios for agent-friendly-mcp

Behavioral test scenarios for this skill, following the baseline/with-skill methodology: run each scenario with a fresh subagent that does NOT have the skill loaded (baseline), then with the skill loaded (treatment), and compare against the assertions.
An assertion the with-skill run misses is a finding against the skill, not against the agent.

## Scenario sets

Every scenario belongs to exactly one set, and the set decides what a baseline pass means.
Never pool the two sets into one score.

- **Representative set** — a fixed roster whose job is to estimate what this skill does to ordinary in-scope work.
  A scenario here is never tightened in response to its own results.
  A baseline that satisfies every assertion is a **result to record**, not a scenario to fix: it is evidence the skill adds nothing on that task, which is precisely what this set exists to detect.
  Editing a representative scenario resets its history; say so in the Results table when you do.
- **Challenge set** — scenarios built to be hard enough to separate the arms and show whether a specific rule lands.
  Here a baseline that passes everything does mean the scenario is too easy; tighten it.
  Because this set selects for baseline failure by construction, its results measure whether a rule lands — never how much the skill helps overall, and never its cost.

Scenarios 1–9 below are **challenge set**: each was built or tightened under the selection rule above.
The representative set holds one scenario (R1), run once per arm, so evidence about ordinary tasks is one datapoint deep — do not cite challenge-set totals as the skill's net benefit.

## How to run

1. **Baseline:** dispatch a subagent with only the scenario prompt below.
   Record which assertions its output satisfies.
2. **Treatment:** dispatch a fresh subagent with the skill content available (or triggered via its description) and the same prompt.
3. **Score:** every assertion is pass/fail with a one-line evidence pointer into the transcript.
   Record results in the table at the bottom.

## Scoring dimensions

Each assertion is one of two kinds; scenarios label which.

- **Scored (protocol / outcome).**
  Defect detection, severity / priority judgment, schema validity, and — for scenarios that supply a task and a tool catalog — first-call correctness, first-repair correctness, and the token / tool-call budgets.
  These are what a run passes or fails on.
- **Non-scored conformance.**
  Report layout (the five-line finding format), the exact `Critical / Major / Minor / Nit` words, and coverage-table cosmetics.
  Recorded for consistency, never the reason a run fails.

Every run records three things beyond the assertion count.

- **Set** — representative or challenge, so the two are never averaged.
- **Regression** — any assertion the baseline satisfied and the treatment missed.
  A regression is a finding against the skill even when the treatment's total is higher; report it explicitly rather than letting a net gain absorb it.
- **Overhead** — the treatment's token and tool-call cost stated against the baseline's, as a ratio, not the treatment's figure alone.
  A skill that buys three assertions for four times the context has a price worth naming.

Outcome-metric mapping is deliberately partial.
First-call success, first-repair success, schema validity, tool-selection accuracy, and token usage are measured only where a scenario runs an executable or replayed task with a supplied catalog (see `agent-friendly-mcp/tests/fixtures/` and `agent-friendly-mcp/references/design-workflow.md` Step 8).
A static design/audit assertion — "the contract describes a symbolic error code", "the schema sets `additionalProperties: false`" — is a **leading indicator** of those outcomes, not a measurement of them, and is labeled as such rather than force-mapped onto a metric it does not observe.

## Scenario 1: Design (application test)

**Prompt:**

> Design the agent-facing MCP server contract for a service wrapping the GitHub Issues REST API.
> The underlying API has these endpoints: list issues, get issue, create issue, update issue, add comment, list comments, lock issue, unlock issue, add labels, remove labels, search issues.
> Produce: the tool list with input schemas, the error shape for at least two failure modes, and whatever discovery surface you think agents need.

**Assertions (with-skill run must satisfy):**

- [ ] Tools are task-completing, not one-per-endpoint: the 11 endpoints collapse to roughly 4–7 tools (§3 granularity rule; e.g., label add/remove folded into update, lock/unlock folded or justified as a named split exception).
- [ ] Tool names are `snake_case`, service-prefixed, verb+noun (§3).
- [ ] Input schemas use `additionalProperties: false`, disambiguated parameter names (`issue_number` not `issue`), and declared omission semantics for optional parameters — `default` only where the server applies it (§3).
- [ ] At least two error payloads use stable symbolic codes with field-level detail and a repair hint naming a real callable surface (§6).
- [ ] Errors return as tool result errors (`isError: true`), not JSON-RPC errors (§6).
- [ ] A capability summary exists stating what the server does NOT do (§1/§2 negative scope).
- [ ] Pagination is cursor-based and provenance-correct: a tool's own list-shaped result payload may use the `has_more` house convention, while native list methods (`tools/list`, etc.) use `nextCursor` (omission = done) — not a house convention; responses also have a concise default with a `detail` toggle (§8).
- [ ] Annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`) are present and honest — e.g., create-issue is not marked read-only or idempotent (§3).
- [ ] **(Scored — per tool, not per catalog.)** Every tool definition the run produces is scored independently against every requirement of `[3.output-schema]`.
  Scenario premise: the tasks this prompt implies — search, read, create, update, comment, label — all return machine-contract fields, as does any discovery or capability-summary tool a run chooses to add, so no tool here is expected to reach that rule's carve-out.
  Fail any tool that violates any part of the rule, and evaluate each claimed carve-out independently.
- [ ] **(Scored.)** The error path is contract-correct and distinct from the success shape: `isError: true` results carry the §6 error envelope in `structuredContent` (with a `content` textual fallback), and `outputSchema` is scoped to **success** results — stated as this skill's reading of an unsettled spec point, not as settled MCP law (`[3.output-schema-scope]`). The design does one of: documents a success-only `outputSchema` with the error envelope validated separately, or unions success and error branches into `outputSchema`. A text-only error carrier counts only when disclosed as a degraded mode (`[6.degraded-carrier]`).

- [ ] **(Scored — disposition honesty.)** Scenario premise: the prompt supplies no runnable server or eval harness.
  The output must therefore satisfy the Step 9 `not-run` disposition in `design-workflow.md`.
  Silently omitting Step 9 or claiming measured improvement fails this assertion.

**Expected baseline failures:** endpoint-mirroring (one tool per endpoint), prose-only error descriptions, no negative scope, no pagination contract, missing or dishonest annotations, no output schema / free-text results, and error results that reuse the success `structuredContent` shape or omit the structured error envelope entirely.

## Scenario 2: Audit (retrieval test)

**Prompt:**

> Audit this MCP server surface for agent-friendliness and report your findings:
>
> ```json
> {
>   "tools": [
>     {"name": "send", "description": "Send a message.", "inputSchema": {"type": "object", "properties": {"channel": {"type": "string"}, "msg": {"type": "string"}}},
>      "annotations": {"readOnlyHint": true}},
>     {"name": "post_message", "description": "Send a message to a channel.", "inputSchema": {"type": "object", "properties": {"channel": {"type": "string"}, "text": {"type": "string"}}}},
>     {"name": "delete_all_messages", "description": "Clear a channel.", "inputSchema": {"type": "object", "properties": {"channel": {"type": "string"}}}}
>   ],
>   "notes": "Server exposes 58 more tools not shown. Errors are returned as the string 'something went wrong'. No resources, no prompts, no pagination."
> }
> ```

**Assertions (with-skill run must satisfy):**

- [ ] **(Scored — defect detection.)** Surfaces the load-bearing defects: the `readOnlyHint` lie on `send`, the `send`/`post_message` overlap, the unstructured error strings, the 61-tool no-reduction gap, and the missing `additionalProperties: false` — independent of how they are worded or labeled.
- [ ] **(Scored — priority judgment, predeclared bands.)** Ranks by impact against `agent-friendly-mcp/references/review-workflow.md` § Severity Scale: the false `readOnlyHint` is highest-priority and merge-blocking; the `send`/`post_message` overlap and the unstructured error strings are at least must-fix / major-equivalent. Score the impact judgment, not the label word.
- [ ] **(Non-scored conformance.)** May use the five-line finding layout and the exact `Critical / Major / Minor / Nit` vocabulary from `agent-friendly-mcp/references/review-workflow.md` § Report Format; recorded, never the reason a run fails.
- [ ] **(Covered by the priority-band bullet above.)** The `readOnlyHint: true` claim on the mutating `send` tool is ranked highest-priority / merge-blocking (§3 annotation honesty); the exact word "Critical" is non-scored.
- [ ] Flags `send` vs `post_message` overlap as a wrong-tool-selection finding (§3).
- [ ] Flags `delete_all_messages` as needing an explicit `destructiveHint: true` and a confirmation boundary (§3 security) — without claiming omission declared it safe, since the spec default for an omitted `destructiveHint` is already `true`.
- [ ] Flags unstructured error strings as Critical or Major against §6 (Critical is defensible when credential failure modes are also collapsed).
- [ ] Flags 61 tools with no client-independent surface reduction (and no progressive-disclosure mechanism) as Major against §2 — not by asserting that `search_tools` alone would shrink what a standard preloading client loads.
- [ ] Flags missing `additionalProperties: false`, ambiguous `channel`/`msg` parameter names (§3).
- [ ] **(Scored — coverage completeness.)** Accounts for every checklist section §1–§9, giving resources (§4) and prompts (§5) an explicit `not-checked` / `N/A` reason rather than silently skipping them.
- [ ] **(Non-scored conformance.)** The specific coverage-table layout is recorded for consistency, not scored.
- [ ] Remediations name real callable surfaces (renamed tools, parameter names), not generic advice.

**Expected baseline failures:** unstructured prose review, misranks the readOnlyHint lie below merge-blocking, no coverage table, misses the `readOnlyHint` lie or rates it as minor, no checklist-section anchoring.

## Scenario 3: Long-running contract (application test)

**Prompt:**

> Design the agent-facing MCP contract for a `video_render` tool whose renders take 1–10 minutes and can pause waiting for the user to approve a watermark.
> Target MCP 2026-07-28 with the `io.modelcontextprotocol/tasks` extension.
> Produce: the capability declarations, the tool definition, the wire shapes an agent sees when creating, polling, and recovering the render, and whatever fallback you think clients without task support need.

**Assertions (with-skill run must satisfy):**

- [ ] Tasks are gated on the extension at both ends: the client's per-request `clientCapabilities.extensions` declaration AND the server's `server/discover` advertisement — the removed `execution.taskSupport` and per-request task opt-in field do not appear (§7).
- [ ] Native task fields use extension casing (`taskId`, `status`, `statusMessage`, `createdAt`, `lastUpdatedAt`, `ttlMs`, `pollIntervalMs`) and statuses are exactly `working`/`input_required`/`completed`/`failed`/`cancelled` (§7).
- [ ] The `CreateTaskResult` carries the task fields inline with `resultType: "task"`, while `tasks/get`/`tasks/update`/`tasks/cancel` results are `resultType: "complete"` — and the removed `tasks/result`/`tasks/list` methods do not appear (§7, native-wire-shapes).
- [ ] Any `progressToken` originates in the request's `_meta`, and post-creation progress rides `statusMessage`/`notifications/tasks`, not `notifications/progress` (§7).
- [ ] The watermark pause is handled via `input_required` with the native recovery path: `tasks/get` carries the outstanding `inputRequests`, the client answers via `tasks/update` `inputResponses`, honoring the client's declared elicitation modes (§7).
- [ ] A tool-result error is modeled as a `completed` task whose `result.isError` is true; `failed` is reserved for JSON-RPC errors and carries `error` (§7).
- [ ] The fallback status/cancel tools are labeled as convention, mirror the native signals (state, when to poll, result location, expiry), and do not replace `tasks/*` (§7).
- [ ] Native fields and house conventions are not mixed: convention metadata is namespaced or labeled, and native casing is never snake_cased (native-vs-convention rule).

**Expected baseline failures:** the 2025-11-25 contract reproduced from memory (`execution.taskSupport`, `tasks/result` holds, `ttl`/`pollInterval` spellings, `result.task` nesting), invented snake_case task fields or statuses (`running`, `succeeded`), tool errors mapped to `failed`, server-minted progress tokens, fallback tools presented as protocol.

## Scenario 4: Instructions and description prose (application test)

**Prompt:**

> You are writing the prose surfaces of an MCP server called `deployctl` that wraps an internal deployment service.
> The tool schemas already exist; your job is ONLY the prose:
>
> 1. The server-level `instructions` string (the capability summary surfaced to agents at connection setup).
> 2. The `description` field text for two tools: `deployctl_deploy_service` and `deployctl_rollback_service`.
>
> Base them on the ops team's notes below (verbatim):
>
> "Deploys go through Spinnaker under the hood, which we adopted back in 2021 after the Jenkins fiasco.
> You generally want to run a dry-run first — it catches most config drift.
> Production deploys need a change ticket, that's an SRE policy thing, and honestly try to avoid deploying on Fridays.
> Rollbacks are pretty safe, they just repoint the release symlink, though if the previous release is more than 30 days old it's been garbage collected so rollback won't work, and you should probably check that first.
> The staging environment sometimes gets wedged; a redeploy usually fixes it.
> Also be careful with the `force` flag — it skips the pre-deploy health checks."
>
> Return exactly: the `instructions` string, then the two description strings, each clearly labeled.

**Assertions (with-skill run must satisfy):**

- [ ] **A1.** Binding rules (change-ticket requirement for production, dry-run expectation, 30-day rollback window, `force` constraint) are structurally distinguishable from background context — imperative sentences or list items, not clauses buried mid-narrative (§2/§3 prose rules).
- [ ] **A2.** Every rule's strength is explicit: mandatory ("requires `change_ticket` when `environment=production`") vs default with override ("prefer `dry_run: true` unless re-running a config already dry-run-validated") — field names in these examples are illustrative, since the prompt does not supply the schemas; score the phrasing pattern, not the identifiers; the source hedges ("generally", "try to", "probably", "honestly") are resolved to one or the other — a resolution the notes don't determine may be marked as an author decision to confirm with the ops team, but is never reproduced as a hedge.
- [ ] **A3.** Every directive is checkable against observable behavior: "be careful with `force`" is replaced by the sourced fact (it skips the pre-deploy health checks) plus either a permitted-use condition or an explicit note that the permitted-use policy is an open author decision — not a fabricated policy presented as sourced; "rollbacks are pretty safe" is replaced by the observable condition (release older than 30 days is garbage-collected and cannot be rolled back).
- [ ] **A4.** Compound notes are split into atomic obligations — the rollback sentence yields separate statements for the symlink mechanics (context) and the 30-day limit (rule).
- [ ] **A5.** Discretionary background (Spinnaker/Jenkins history, "adopted in 2021") is dropped or kept clearly apart from the rules, never interleaved with them; soft norms (Friday deploys) are either stated as an explicit default with override or dropped, not echoed as vibes.

**Expected baseline failures:** narrative paragraphs that reproduce the ops notes' structure, hedges carried through verbatim ("generally", "be careful"), rules embedded mid-sentence next to Spinnaker trivia, compound sentences bundling mechanics with constraints.

## Scenario 5: Resources (application test)

**Prompt:**

> Design the agent-facing MCP resource surface for a server that exposes a large internal documentation wiki to an agent.
> The wiki has thousands of pages organized in spaces (e.g. `eng`, `hr`); pages can be large (some over 100 KB); page content changes during the day; and agents need to look up a specific page by space + slug as well as browse.
> Produce: the resource URI scheme, what a resource index/list entry looks like versus a full body, how large pages are delivered, how an agent discovers parameterized lookups, how an agent is notified when a page it cares about changes, and any fallback for clients that do not handle resources well.

**Assertions (with-skill run must satisfy):**

- [ ] Resource URIs are stable, hierarchical, and use domain nouns (e.g. `wiki://spaces/{space}/pages/{slug}`), not internal numeric ids that change between deployments (§4).
- [ ] Index/list entries carry native triage metadata — `title`, `description`, `mimeType`, `size`, `annotations.lastModified` — and do NOT inline the page body; the summary is short (at most three sentences) (§4).
- [ ] Large page bodies are chunkable, and every chunk has its own callable URI published as a resource template (`resources/templates/list` with `uriTemplate`) — because native `resources/read` takes only a URI — or a labeled tool fallback that accepts a chunk id (§4).
- [ ] Chunk identifiers are stable across reads of the same page version, and a version change is observable via the resource's modification metadata (§4).
- [ ] Custom/index metadata with no native field rides under a namespaced `_meta` key, never as a new top-level field on the `Resource` record (§4, native-vs-convention).
- [ ] Mutable pages support subscriptions: the server advertises `resources.subscribe`, serves the `resourceSubscriptions` filter of `subscriptions/listen`, and emits `notifications/resources/updated` (tagged with `subscriptionId`) for watched URIs — distinguished from `notifications/resources/list_changed`, which signals catalog membership changes, not body edits (§4).
- [ ] Parameterized lookups are exposed via resource templates, with completion for `{space}`/`{slug}` where clients negotiate `completions`, so an agent can construct a page URI without enumerating every page (§4).
- [ ] A tool fallback reaches the same indexed content and is self-sufficient from `tools/list` alone, for clients that do not expose resources well (§4).

**Expected baseline failures:** unstable or numeric-id URIs, index entries that inline full bodies or omit `size`/`lastModified`, whole-document delivery with no chunking or chunk URIs, custom fields added at the top level of the resource record, `list_changed` conflated with per-resource update notifications (or no subscription mechanism at all), no resource-template or completion discovery, no tool fallback.

## Scenario 6: Prompts (application test)

**Prompt:**

> Design a reusable MCP prompt named `open_incident` for a server that wraps an incident-management service.
> Its tools already exist: `incident_create`, `incident_add_responder`, `incident_post_update`, plus a resource `incidents://active`.
> The prompt should help an agent run the "declare a new incident" workflow.
> Produce: the prompt definition (name, arguments, and any orchestration text), and a short note on what belongs in the prompt versus what belongs in the tool and resource schemas.

**Assertions (with-skill run must satisfy):**

- [ ] The prompt references its follow-on tools and resource by canonical name (`incident_create`, `incident_add_responder`, `incident_post_update`, `incidents://active`) and does NOT redefine their argument shapes or contracts (§5).
- [ ] Prerequisites are declared — which tools, which resources, and which permission or context assumptions the prompt relies on (§5).
- [ ] No behavior is load-bearing in the prompt text: apply the "remove every prompt — is any tool now unsafe or uncallable?" audit; argument shapes, side effects, and error handling live in the tool schemas, not the prompt prose (§5).
- [ ] Only native `PromptArgument` fields appear on each argument (`name`, `title`, `description`, `required`); value-shape guidance (types, enums, defaults, arrays) is carried in each argument's `description`, not as non-native keys such as `type`/`items`/`default` (§5, native-vs-convention).
- [ ] Any convention metadata (when-to-use, prerequisites, expected-followups) rides under a namespaced `_meta` key, not as top-level `Prompt` fields (§5, native-vs-convention).
- [ ] Completion is offered for arguments with dynamic value sets (e.g. a service or team the agent should not guess) where `completions` is negotiated (§5).
- [ ] The design states explicitly that the prompt is optional orchestration scaffolding — a client that never invokes it (most code-execution clients) can still call every tool correctly from the schemas alone (§5).

**Expected baseline failures:** prompt redefines tool argument shapes inline, encodes required behavior (side effects or error handling) in prose so a schema-only client would call wrong, uses non-native argument keys (`type`/`items`/`default`) or top-level convention fields, no declared prerequisites, no completion, treats the prompt as required rather than optional.

## Scenario 7: Triggering (activation test)

Unlike Scenarios 1–6, this scenario tests whether the skill's `description` fires at all, so baseline/treatment does not apply — loading the skill is the dependent variable.

**Method.**

1. Present the skill alongside a realistic catalog of sibling skills, in randomized order, with the prompt blind to the expected answer.
2. Prefer the host's real selector and verify an observable skill-load/read event before task execution.
   Where the harness exposes no such signal, fall back to a labeled description-classifier proxy: ask a dispatcher "which of these skills, if any, applies?" — recorded as a **proxy**, not proof the host loads the skill.
3. Run each case several times with a pinned model/runtime and report a **trigger rate**, not a single pass/fail.

**Cases — close-boundary minimal pairs (grounded in `agent-friendly-mcp/SKILL.md` § When To Use / § When Not To Use):**

| # | Prompt (abbreviated) | Expected |
| --- | --- | --- |
| T1 | "Design the MCP server contract for our billing API so agents can call it." | fire |
| T2 | "Review the internal Python of our MCP server for dead code and style." | quiet (non-agent-facing internals, `agent-friendly-mcp/SKILL.md` § When Not To Use — "General code review of MCP server internals") |
| T3 | "Harden the input schemas on our `deploy` and `rollback` MCP tools — agents keep passing ambiguous args." | fire |
| T4 | "Add one optional `note` field to a tool on our already agent-friendly MCP server." | quiet (trivial addition, `agent-friendly-mcp/SKILL.md` § When Not To Use — "Trivial schema additions") |
| T5 | "Design the recovery + progress contract for a 5-minute MCP render task." | fire |
| T6 | "Design the operator dashboard that shows our MCP server's request volume." | quiet (operator dashboard, `agent-friendly-mcp/SKILL.md` § When Not To Use — "server-operator dashboards") |
| T7 | "Write the client code that calls the `incidents://active` resource on someone else's MCP server." | quiet (consuming, not designing) |
| T8 | "Our agents keep picking the wrong tool out of the 60 we expose — help." | fire (symptom, no literal "MCP server") |

**Assertions:**

- [ ] **(Scored — trigger recall.)** T1, T3, T5, T8 fire at a high rate; report the rate per case.
- [ ] **(Scored — trigger precision.)** T2, T4, T6, T7 stay quiet at a high rate; a fire on any of these is a precision finding against the `description`, not against the agent.
- [ ] **(Recorded.)** Whether the run used the host's real selector or the labeled classifier proxy, and the model/runtime and trial count.

**Expected description weaknesses (findings against the skill if seen):** T8 (symptom without "MCP server") fails to fire — the description leans on the literal term; T2 or T7 fire — the description over-matches on the keyword "MCP" regardless of design-vs-consume or agent-facing-vs-internal.

## Scenario 8: Severity calibration on a minimal server (audit test)

Scenario 2 exercises a broad, ambiguous surface where the missing capability summary is correctly severe.
This scenario is its mirror: a surface small and self-sufficient enough that the same absence should scale *down*.

**Baseline note.** A no-skill baseline cannot exercise a severity scale it does not have, so the discriminating contrast here is the skill's own wording across versions: the pre-#125 text (missing summary is Major by default, escalating only upward) against the current text.
Record which wording a run was scored against.

**Prompt:**

> Audit this MCP server surface for agent-friendliness and report your findings:
>
> ```json
> {
>   "serverInfo": {"name": "ups-tracking", "title": "UPS Package Tracking", "version": "2.1.0"},
>   "tools": [
>     {
>       "name": "ups_track_package",
>       "title": "Track a UPS package",
>       "description": "Return the current status and scan history for one UPS tracking number.\n\nWhen to use: the user has a UPS tracking number and wants its delivery status or scan history. This server tracks only — it does not create, modify, or void shipments, does not validate addresses, does not quote rates, and does not cover carriers other than UPS.\n\nPrerequisites: none beyond the server's own configured UPS API credential. No user account, workspace selection, or prior call is required.\n\nExample: ups_track_package(tracking_number=\"1Z999AA10123456784\", detail=\"full\")",
>       "inputSchema": {
>         "$schema": "https://json-schema.org/draft/2020-12/schema",
>         "type": "object",
>         "properties": {
>           "tracking_number": {"type": "string", "pattern": "^1Z[0-9A-Z]{16}$", "description": "The 18-character UPS tracking number as printed on the label."},
>           "detail": {"type": "string", "enum": ["summary", "full"], "default": "summary", "description": "Response density. Omitted means 'summary' (the server applies this default): latest scan only. 'full' returns the complete scan history."}
>         },
>         "required": ["tracking_number"],
>         "additionalProperties": false
>       },
>       "outputSchema": {"type": "object", "properties": {"status": {"type": "string"}, "delivered_at": {"type": ["string", "null"], "format": "date-time"}, "scans": {"type": "array"}}, "required": ["status"], "additionalProperties": false},
>       "annotations": {"readOnlyHint": true, "openWorldHint": true}
>     }
>   ],
>   "notes": "This is the server's entire agent-facing surface: one tool, no resources, no prompts, no other tools hidden behind pagination. Errors return a structured envelope with symbolic codes (`invalid_tracking_number`, `carrier_unavailable`, `rate_limited`), field-level detail, and repair hints naming real arguments. The server publishes no capability summary: no summary resource, no discovery tool, and its `server/discover` result carries no `instructions` field."
> }
> ```

**Assertions (with-skill run must satisfy):**

- [ ] **(Scored — the finding is still recorded.)** The absent capability summary is recorded as a finding against §2/§1, not silently dropped. Scaling severity down is not permission to omit.
- [ ] **(Scored — severity calibration.)** That finding is rated **Minor**. A Major or Critical rating here is a finding against `review-workflow.md`, not against the agent.
- [ ] **(Scored — evidence named.)** The Minor rating cites positive cold-start evidence — that a cold start reaches a correct first call from the tool definition alone — plus the small catalog and the definition's self-sufficiency on scope, negative scope, and prerequisites. A rating that names no evidence fails this assertion even when the band is Minor, because the wording makes Major the fallback for unplaced findings.
- [ ] **(Scored — the scale moved, not the report.)** Scaling this finding down is not compensated by inflating *it* through a different section — the summary's absence is not re-entered as a Critical §1 finding, or as a Major discovery finding, under another name. Other findings this fixture genuinely supports are not inflation: the surface deliberately carries real defects elsewhere (no credential-failure code among the three symbolic codes, and a `tracking_number` pattern that rejects valid non-1Z UPS formats), and reporting those at Major is correct. A run that reports nothing but the summary finding is not passing harder — it is missing the fixture's other defects.
- [ ] **(Scored — negative scope is credited, not re-flagged.)** The run does not report missing negative scope (§2): the tool description states what the server does not do. Re-flagging it is a false positive.
- [ ] **(Non-scored conformance.)** Five-line finding layout, exact severity vocabulary, and coverage-table cosmetics.

**Expected failure under the pre-#125 wording:** the missing summary lands at Major on the strength of the house default, with no evidence named — the inflation #125 was filed about — or the run reaches Minor but justifies it only by the *absence* of failure evidence rather than positive cold-start evidence.

## Scenario 9: Instructions laid out for a truncated prefix (audit test)

Scenario 4 tests how `instructions` prose is phrased; this one tests where the binding content sits in it, and whether the audit stays client-neutral about truncation.
The fixture's `instructions` string is 2,736 ASCII characters. Measured as zero-based offsets: the background history ends at 1,296, the error-field glossary ends at 2,153, the line "Note: some clients may truncate these instructions." starts at 2,155, and every binding rule follows the `Rules:` header at 2,208.
None of the four tools' descriptions or schemas restates those rules.
Those offsets are for scoring only and are not given to either arm.

**Prompt:**

> Audit the server-level `instructions` string and the tool descriptions of this MCP server for agent-friendliness.
> Its operators target two MCP clients: Claude Code and Codex CLI.
> Report your findings with a severity and a concrete remediation for each.
>
> ```json
> {
>   "serverInfo": {
>     "name": "ledgerline",
>     "title": "Ledgerline Bookkeeping",
>     "version": "3.2.0"
>   },
>   "instructions": "Ledgerline connects agents to the Ledgerline bookkeeping platform, which small-business accountants use to manage client ledgers, invoices, and reconciliations. Ledgerline began in 2014 as an internal tool at a regional accounting firm and was spun out as a product in 2017; the MCP server was added in 2025 so that assistants could help accountants with routine ledger work. The server was rewritten in 2026 on the Ledgerline public API, replacing an earlier integration that scraped the web interface, and it now shares that API's authentication and audit logging. Accountants typically use it for month-end close: reviewing unposted entries, correcting miscategorized transactions, and preparing the ledger for review by a senior partner. The platform stores each client's books as a project, and every project holds accounts, journal entries, invoices, and bank feeds. Most accountants manage between ten and forty client projects, and many of them keep one project per fiscal year for archival reasons, so project names often repeat with a year suffix. The server exposes tools for listing projects, reading and posting journal entries, and voiding entries, and it also offers read access to invoices. It does not file taxes, move money, connect bank accounts, or send invoices to customers.\n\nError envelope reference: every failed call returns an error object with these fields. `code` is a stable symbolic identifier such as `project_not_found`, `entry_locked`, `period_closed`, or `rate_limited`. `message` is a human-readable sentence intended for display to the accountant. `field` names the input argument that caused the failure, when one did. `allowed` lists the accepted values for that field, when the set is small. `retryable` is a boolean; `true` means the same call may succeed later, and `false` means it will not. `retry_after_ms` appears only on `rate_limited` and says how long to wait. `repair` carries a suggested next call, with `tool` and `arguments` keys. `request_id` correlates the failure with server logs and should be quoted when the accountant contacts support. `docs_url` points at the help-center article for the code.\n\nNote: some clients may truncate these instructions.\n\nRules:\n- Call ledgerline_list_projects before any project-scoped call, and pass the returned project_id; project names are not unique and are never accepted as identifiers.\n- ledgerline_void_entry is irreversible: it requires a confirm_token obtained from ledgerline_void_entry with dry_run=true, and the token expires after 5 minutes.\n- Never post or void entries in a closed period; check the period_status field of the project first, and treat period_closed errors as non-retryable.\n- Keep to 30 calls per minute per project.",
>   "tools": [
>     {
>       "name": "ledgerline_list_projects",
>       "title": "List client projects",
>       "description": "List the accountant's client projects with their ids, names, fiscal years, and period status.",
>       "inputSchema": {
>         "type": "object",
>         "properties": {
>           "cursor": {
>             "type": "string",
>             "description": "Opaque cursor from a previous call."
>           }
>         },
>         "required": [],
>         "additionalProperties": false
>       },
>       "annotations": {
>         "readOnlyHint": true
>       }
>     },
>     {
>       "name": "ledgerline_get_entries",
>       "title": "Read journal entries",
>       "description": "Return journal entries for one project, newest first.",
>       "inputSchema": {
>         "type": "object",
>         "properties": {
>           "project_id": {
>             "type": "string",
>             "description": "Project identifier."
>           },
>           "since": {
>             "type": "string",
>             "format": "date",
>             "description": "Only entries on or after this date."
>           }
>         },
>         "required": [
>           "project_id"
>         ],
>         "additionalProperties": false
>       },
>       "annotations": {
>         "readOnlyHint": true
>       }
>     },
>     {
>       "name": "ledgerline_post_entry",
>       "title": "Post a journal entry",
>       "description": "Post a balanced journal entry to a project.",
>       "inputSchema": {
>         "type": "object",
>         "properties": {
>           "project_id": {
>             "type": "string",
>             "description": "Project identifier."
>           },
>           "date": {
>             "type": "string",
>             "format": "date"
>           },
>           "lines": {
>             "type": "array",
>             "description": "Debit and credit lines; debits must equal credits.",
>             "items": {
>               "type": "object",
>               "properties": {
>                 "account": {
>                   "type": "string"
>                 },
>                 "debit": {
>                   "type": "number"
>                 },
>                 "credit": {
>                   "type": "number"
>                 }
>               },
>               "required": [
>                 "account"
>               ],
>               "additionalProperties": false
>             }
>           }
>         },
>         "required": [
>           "project_id",
>           "date",
>           "lines"
>         ],
>         "additionalProperties": false
>       },
>       "annotations": {
>         "readOnlyHint": false,
>         "destructiveHint": false,
>         "idempotentHint": false
>       }
>     },
>     {
>       "name": "ledgerline_void_entry",
>       "title": "Void a journal entry",
>       "description": "Void a posted journal entry.",
>       "inputSchema": {
>         "type": "object",
>         "properties": {
>           "project_id": {
>             "type": "string",
>             "description": "Project identifier."
>           },
>           "entry_id": {
>             "type": "string",
>             "description": "Entry to void."
>           },
>           "dry_run": {
>             "type": "boolean",
>             "default": false,
>             "description": "Preview the void without applying it."
>           },
>           "confirm_token": {
>             "type": "string",
>             "description": "Token confirming the void."
>           }
>         },
>         "required": [
>           "project_id",
>           "entry_id"
>         ],
>         "additionalProperties": false
>       },
>       "annotations": {
>         "readOnlyHint": false,
>         "destructiveHint": true,
>         "idempotentHint": false
>       }
>     }
>   ]
> }
> ```

**Assertions (with-skill run must satisfy):**

- [ ] **A1 (position).** Identifies that the binding rules (project-id prerequisite, void confirmation, closed-period check, rate limit) come last, after the background and glossary, and that a client delivering only a prefix of `instructions` would drop them.
- [ ] **A2 (reorder).** The remediation moves the binding rules to the head of the string, ahead of the history and the glossary.
- [ ] **A3 (glossary).** Cuts the error-field glossary down to what the agent must branch on (for example which field or value means do not retry) and moves the rest out of the string or drops it, because the error payload carries its own fields when it arrives.
- [ ] **A4 (second carrier).** The rules that govern a specific call (the `ledgerline_list_projects` prerequisite, the `dry_run`/`confirm_token` flow on `ledgerline_void_entry`, the period check before posting or voiding) are also required on that tool's description or schema, not only in `instructions`.
- [ ] **A5 (actionable truncation signal).** Flags "some clients may truncate these instructions" as something an agent cannot act on, and proposes a check the agent can run on its own copy, such as a known final line and what to read when it is missing.
- [ ] **A6 (no borrowed figure).** States no single truncation length as applying to both named clients or to clients in general. Any figure given is attributed to one client and marked as that client's documented or measured behavior, or the budget is left to measurement on each client. Asserting that Codex CLI, or MCP clients generally, cut at 2,048 characters or 2 KB fails.

**Expected baseline failures:** the rules are rewritten for clarity but left in place, or the glossary is kept as is; the truncation note is kept or reworded rather than replaced by a check; any length budget is stated as a general client limit.

## Representative set

### R1: Small read-only service (application test)

A deliberately ordinary in-scope task: small surface, no trap, no rule this scenario was built to catch.
It exists to answer the question the challenge set cannot — what the skill does to routine work — so a baseline that passes every assertion is the finding, not a defect in the scenario.
Do not tighten these assertions in response to a run.

**Prompt:**

> Design the agent-facing MCP server contract for a service wrapping an internal package registry.
> The underlying API has three read endpoints: search packages, get package metadata, list versions of a package.
> Produce the tool list with input schemas, an output contract, and the error shape for a missing package.

**Assertions (both arms scored identically):**

- [ ] Tool names are `snake_case`, service-prefixed, verb+noun (`[3.naming]`).
- [ ] Input schemas set `additionalProperties: false` on every object (`[3.closed-schemas]`).
- [ ] Parameter names are unambiguous about what they identify — `package_name`, not `name` (`[3.param-names]`).
- [ ] Read tools carry `readOnlyHint: true` with the mutation hints omitted, not defaulted (`[3.annotation-defaults]`).
- [ ] Each tool publishes an `outputSchema` and returns `structuredContent` (`[3.output-schema]`, scored per tool).
- [ ] The `content` fallback does not contradict `structuredContent` (`[3.content-types]`).
- [ ] The missing-package failure returns a tool result error with a stable symbolic code and a repair hint naming a real callable surface (§6).
- [ ] A capability summary states what the server does NOT do (§1/§2 negative scope).

**Record:** set, regression, and overhead per the Scoring dimensions above.

## Results

Every row is scored against the assertion text in force at its recorded tree, not against the current text.
Where a later change tightens an assertion and restates a score, the row carries both figures and names the issue that tightened it; the restatement lives here, never rewritten into the run file.
A run file's own text is edited only to correct a claim that was factually wrong about what that run produced, judged against the assertions in force when it was written — never to track a later assertion change, and never to restate a score.
Such a correction is recorded in the run file as a dated erratum quoting the sentence it replaces, so the original claim stays legible.
Rows dated before 2026-07-29 additionally measured the MCP 2025-11-25 contract that the skill taught at the time (see `agent-friendly-mcp/decisions/001-mcp-2026-07-28-rebase.md`), and their evidence files are immutable historical artifacts — the erratum allowance above does not reach them, and a factual error in one is noted in its Results row instead.

| Date | Scenario | Run | Assertions passed | Notes |
| --- | --- | --- | --- | --- |
| 2026-09-04 | R1 (small read-only service) | baseline | 4/8 | **Representative set**, Fable 5 subagent, zero tool calls (answered from memory as instructed). Passed closed input schemas, per-tool `outputSchema`+`structuredContent`, non-contradicting `content` ("one source of truth"), and a symbolic `PACKAGE_NOT_FOUND` whose recovery hint names the real `search_packages` tool. Failed service-prefixed naming (`get_package`, undocumented namespace assumption), the annotation gate (asserted `idempotentHint: true` on read-only tools), and agent-facing negative scope (a design-doc "Deliberate exclusions" section, not a summary exposed to agents). Cost: 25,892 tokens, 0 tool calls, ~1,150 words out. |
| 2026-09-04 | R1 (small read-only service) | treatment | 7/8 | **Representative set**, Fable 5 subagent, same prompt and model as the baseline row. Took the **full walk** and said so, correctly reading the new route rule as barring the focused route for a new server. Passed naming, closed schemas, the annotation gate (mutation hints omitted, citing `[3.annotation-defaults]`), per-tool `outputSchema`, `content`/`structuredContent` agreement, the §6 envelope with a callable `repair`, and an explicit `does_not` array. **Regressions: none** — it passed every assertion the baseline passed. Cost: 97,485 tokens, 7 tool calls, ~3,400 words out — **3.8× the baseline's tokens for +3 assertions**. |
| 2026-09-04 | R1 | finding against the skill | A3 missed by both arms | `[3.param-names]` requires disambiguated parameter names, and the treatment read §3 in full and still named the parameter `name` rather than `package_name` — the same choice the baseline made. One rule the skill did not transmit on an ordinary task; the first representative-set evidence of a non-effect. Diagnosis: `[3.param-names]`'s examples covered only the *form* ambiguity (`user_id` over `user`), never the *entity* ambiguity (`package_name` over `name`), so the rule under-determined this case; the entity form was added to the rule in the same change. Not yet re-run against the amended rule. |
| 2026-06-09 | 2 (audit) | baseline | 5/9 | Caught readOnlyHint lie, duplication, error strings, tool count, naming — but no severity scale (used Critical/High/Medium), no five-line format, no §-anchoring, no coverage table, no N/A entries for resources/prompts. |
| 2026-06-09 | 2 (audit) | with-skill | 9/9 | Five-line findings F1–F7 anchored to §N; coverage table with not-checked reasons; six probes run, three skipped with reasons; remediations name `chat_send_message`, `channel_id`, `search_tools`. Errors rated Critical (within loosened assertion). |
| 2026-07-11 | 1 (design) | baseline | 4/9 | Tree `d586ce3`. Passed A3/A4/A5/A8; failed granularity (11 endpoint-mirroring tools), naming (no service prefix, noun_verb), negative scope, pagination provenance/detail-toggle, and shown `outputSchema` (claimed in prose only). [evidence](runs/2026-07-11-scenario1-baseline.md) |
| 2026-07-11 | 1 (design) | with-skill | 9/9 as scored; **8/9** rescored (#122) | Tree `d586ce3`. Rescored 2026-07-30 against the tightened per-tool A9: the run shows 7 tools and one `outputSchema` (on `github_search_issues`), which the original cell already disclosed. Evidence file left byte-for-byte unchanged. 11 endpoints → 7 task-completing `github_*` tools with justification table; explicit `does_not`; house pagination labeled vs native `nextCursor`; `outputSchema` on the flagship read tool; one-envelope-two-carriers errors. [evidence](runs/2026-07-11-scenario1-with-skill.md) |
| 2026-07-11 | 3 (long-running) | baseline | 4/7 | Tree `d586ce3`, 2025-11-25 contract. Passed A1/A2/A3/A7; failed A4 (invented `notifications/tasks/status` instead of request-`progressToken`), A5 (polled instead of preemptive-hold `tasks/result`), A6 (fallback not labeled convention, no expiry). Caveat: A1 used `requests: ["tools/call"]` array vs spec nested shape. [evidence](runs/2026-07-11-scenario3-baseline.md) |
| 2026-07-11 | 3 (long-running) | with-skill | 7/7 | Tree `d586ce3`, 2025-11-25 contract. Nested `tasks.requests.tools.call`; request-originated `progressToken`; preemptive-hold `input_required` recovery via `elicitation/create`; labeled-convention fallback mirroring expiry/result-location; `tasks/list` withheld for isolation. [evidence](runs/2026-07-11-scenario3-with-skill.md) |
| 2026-07-11 | 5 (resources) | baseline | 5/8 | Tree `d586ce3`. Passed URIs/chunk-templates/version-pinning/subscriptions/tool-fallback; failed native triage field names (used `summary`/`sizeBytes`/`updatedAt`), non-namespaced `_meta`, and no completion on templates. [evidence](runs/2026-07-11-scenario5-baseline.md) |
| 2026-07-11 | 5 (resources) | with-skill | 8/8 | Tree `d586ce3`. Native `size`/`annotations.lastModified` triage fields; namespaced `_meta` (`com.acme-wiki/*`); `completion/complete` for `{space}`/`{slug}`; bounded `resources/list`; one-envelope-two-carriers resource failures. [evidence](runs/2026-07-11-scenario5-with-skill.md) |
| 2026-07-11 | 6 (prompts) | baseline | 5/7 | Tree `d586ce3`. Passed canonical-name refs, native `PromptArgument` fields, workflow-vs-schema split, no top-level convention fields; failed declared prerequisites and completion on dynamic arguments. [evidence](runs/2026-07-11-scenario6-baseline.md) |
| 2026-07-11 | 6 (prompts) | with-skill | 7/7 | Tree `d586ce3`. Prerequisites block + convention metadata under namespaced `_meta` (`com.incident-mcp/*`); completion for `severity`/`responders`/`commander`; explicit "delete the prompt — does anything break?" §5 audit; contract kept in tool/resource schemas. [evidence](runs/2026-07-11-scenario6-with-skill.md) |
| 2026-07-02 | 4 (prose) | baseline (skill pre-§2/§3/§4 prose rules) | 1/5 | `force` fact and 30-day condition checkable (A3 pass), but description rules buried mid-narrative and the dry-run rule left in a workflow paragraph (A1 fail), "Recommended workflow" dry-run carries no override condition (A2 fail), one bullet bundles previous-release-only + 30-day GC + recovery action (A4 fail), rollback mechanics interleaved with eligibility rules (A5 fail). |
| 2026-07-02 | 4 (prose) | with-skill | 5/5 | Labeled `Rules:`/`Background:` sections; every rule mandatory or default-with-override; `force` carries the sourced fact plus an explicit permitted-use condition. Two earlier iterations were discarded: the first with-skill run echoed the guidance's then-deploy-domain examples (checklist examples moved to a messaging domain in response), and Codex review flagged that the prompt omitted `force` semantics so a pass could reward invented policy (sourced fact added to the notes). The scores above are the final runs against the corrected prompt. |
| 2026-07-11 | 2 (audit) | baseline | 2/9 | Tree `a3cd37f`. Rescored against the rewritten scoring (defect detection + priority bands; layout/vocabulary non-scored). No predeclared severity bands or §-anchoring, missed `additionalProperties: false`, generic remediations. [evidence](runs/2026-07-11-scenario2-baseline.md) |
| 2026-07-11 | 2 (audit) | with-skill | 9/9 | Tree `a3cd37f`. Rescored against the rewritten scoring. Impact-ranked findings (readOnlyHint lie merge-blocking), §-anchored, full §1–§9 coverage table with N/A reasons, concrete renamed-surface remediations. [evidence](runs/2026-07-11-scenario2-with-skill.md) |
| 2026-07-11 | 4 (prose) | baseline | 1/5 | Tree `a3cd37f`. Rerun on the pinned tree. Binding rules not separated from narrative (A1), Friday soft-norm + dry-run hedge unresolved (A2/A5), rollback mechanics compound-bundled with the 30-day rule (A4); A3 pass. [evidence](runs/2026-07-11-scenario4-baseline.md) |
| 2026-07-11 | 4 (prose) | with-skill | 5/5 | Tree `a3cd37f`. Rerun on the pinned tree. Labeled Rules/Background/When-to-use blocks, mandatory-vs-default-with-override phrasing, hedges removed. [evidence](runs/2026-07-11-scenario4-with-skill.md) |
| 2026-07-11 | 1 (design, outputSchema-on-error) | with-skill | PASS | Tree `a3cd37f`. Focused error-path probe of the new §3/§6 assertion: every error result sets `isError: true` with the §6 envelope in `structuredContent` + `content` fallback; `outputSchema` scoped to success (stated as the skill's reading of an unsettled point). Baseline expectation (documented): error results reuse the success shape or omit the envelope. [evidence](runs/2026-07-11-scenario1-outputschema-error.md) |
| 2026-07-11 | 7 (trigger) | proxy | recall 4/4, precision 4/4 | Tree `a3cd37f`. Labeled classifier **proxy** (Haiku 4.5), 3 trials/case, randomized 7-skill catalog. T1/T3/T5/T8 fire 12/12; T2/T4/T6/T7 quiet 12/12. Anticipated weaknesses (T8 symptom miss, T2/T7 keyword over-match) did not appear. Not the host's real selector. [evidence](runs/2026-07-11-scenario7-trigger.md) |
| 2026-07-29 | 1 (design) | baseline | 7/10 | Tree `1b0b743` (2026-07-28 rebase), Fable 5 subagent. Strong baseline: 6 task-completing tools, honest annotations, negative scope, actionable errors, detail toggle. Failed service-prefix naming, prose-only `outputSchema` claim (none shown), and the A10 error-path/`outputSchema`-scope rule. [evidence](runs/2026-07-29-scenario1-baseline.md) |
| 2026-07-29 | 1 (design) | with-skill | 10/10 as scored; **9/10** rescored (#122) | Tree `1b0b743`, Fable 5 subagent. Rescored 2026-07-30 against the tightened per-tool A9: 8 tools defined, 7 with an `outputSchema`; `github_get_capabilities` has none. The run file's A9 evidence sentence ("shown per tool") was factually wrong under the original assertion too and was corrected in place. 11 endpoints → 7 `github_*` tools + discovery fallback with a named split exception; shown closed `outputSchema`s with `structuredContent`/`content` pairing; success-scoped `outputSchema` citing `[3.output-schema-scope]`; labeled house pagination vs native `nextCursor`; `[6.rename]` + disclosed `[6.offending-value]` omission policy applied. [evidence](runs/2026-07-29-scenario1-with-skill.md) |
| 2026-07-29 | 3 (long-running) | baseline | 2/8 | Tree `1b0b743` (first run of the rewritten 2026-07-28 assertions), Fable 5 subagent. Reproduces the 2025-11-25 contract from memory: `initialize`-time capabilities, `ttl`/`pollInterval` spellings, `result.task` nesting, removed `tasks/list` and `elicitation/create`+`related-task`, tool errors mapped to `failed`, blocking-call fallback. Passed only progress discipline (A4) and native-vs-convention hygiene (A8). [evidence](runs/2026-07-29-scenario3-baseline.md) |
| 2026-07-29 | 3 (long-running) | with-skill | 8/8 | Tree `1b0b743`, Fable 5 subagent. Per-request `_meta` + `server/discover` gating; `resultType: "task"` create with inline fields; `tasks/get`→`inputRequests`→`tasks/update` watermark recovery honoring declared elicitation modes; `completed`-is-delivery with worked `isError` example; labeled convention fallback mirroring native signals; `Mcp-Name`=taskId transport headers. [evidence](runs/2026-07-29-scenario3-with-skill.md) |
| 2026-07-29 | 5 (resources) | baseline | 6/8 | Tree `1b0b743`, Fable 5 subagent. Improved over 2026-07-11 (native triage names now known; no custom-field violations); failed chunk-id/version stability (A4) and the 2026-07-28 subscription mechanics — used the retired `resources/subscribe` request instead of `subscriptions/listen` + `resourceSubscriptions` with `subscriptionId` tagging (A6). [evidence](runs/2026-07-29-scenario5-baseline.md) |
| 2026-07-30 | 1 (design) | with-skill | 11/11 | Tree `36f6096`, Fable 5 subagent. First run against the tightened per-tool A9 and the new `not-run` assertion: 11 endpoints → 6 `github_*` tools, all 6 publishing an `outputSchema` (machine-counted), and Step 9 recorded `not-run` naming the absent host and harness. Does not reproduce the 2026-07-29 failure shape — this design ships no discovery tool, so a catalog that adds one remains untested. No baseline run at this tree. [evidence](runs/2026-07-30-scenario1-with-skill.md) |
| 2026-07-30 | 8 (severity calibration) | control (pre-#125 wording) | n/a — rated **Major** | Tree `f733b93`, Fable 5 subagent. The control arm for the pair below; it names the house default as its reason ("a missing summary is Major by default"), which is the inflation #125 was filed about. [evidence](runs/2026-07-30-scenario8-severity-calibration.md) |
| 2026-07-30 | 8 (severity calibration) | treatment (#125 wording) | 5/5 — rated **Minor** | Tree `f733b93` + the #125 edit only, Fable 5 subagent. Same fixture and model as the control; only `review-workflow.md` differed. Cites simulated cold-start evidence, the one-tool catalog, and definition self-sufficiency; both arms found the same defects elsewhere, so the change scaled one finding down rather than softening the report. One trial per arm — establishes the wording can move the rating, not a rate. [evidence](runs/2026-07-30-scenario8-severity-calibration.md) |
| 2026-07-29 | 5 (resources) | with-skill | 8/8 | Tree `1b0b743`, Fable 5 subagent. `subscriptions/listen` with `resourceSubscriptions` filter and `subscriptionId`-tagged updates, distinguished from `list_changed`; chunk-id stability pinned to page version with `chunk_stale` repair; native triage fields; namespaced `_meta`; honest `ttlMs`/`cacheScope` per `[8.cacheable-results]`. [evidence](runs/2026-07-29-scenario5-with-skill.md) |
| 2026-09-26 | 9 (instructions prefix) | baseline | 5/6 | Tree `b878505`, Fable 5.1 subagent, prompt file only. Moved the rules first, cut the glossary to a branch rule, put each rule on its tool, and attributed 2,048 to Claude Code alone; failed A5 (deleted the truncation note with no replacement check). Confound: it saw truncated instructions in its own Claude Code context. 57,975 tokens, 3 tool uses. [evidence](runs/2026-09-26-scenario9.md) |
| 2026-09-26 | 9 (instructions prefix) | with-skill | 6/6 | Tree `b878505`, Fable 5.1 subagent, isolated skill copy. Measured offsets, cited per-client figures to decision 006, drafted a 1,267-character replacement with an `END` line check. Only A5 separates the arms, so the scenario needs tightening before it can show A1–A4 or A6 land. 138,119 tokens, 16 tool uses. [evidence](runs/2026-09-26-scenario9.md) |
