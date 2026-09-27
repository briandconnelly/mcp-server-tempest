# 005 — What a `content` fallback block must hold

Decided 2026-09-04.
Triggered by an external review of this skill, which reported that `tests/validate_fixture.py` accepted any non-empty text where the checklist required "parser-compatible JSON in `content`".

## Question

`[3.output-schema]` said to keep parser-compatible JSON in `content`.
`[3.content-types]` said to use `content` for human rendering.
Both are normative, they pull in different directions, and the fallback validator enforced neither.
What must a `content` block hold, and what can a validator check?

## Evidence

The reproduction was confirmed: replacing both fallback text blocks in `tests/fixtures/github_issues.json` with `"not JSON"` produced zero validation issues, while emptying the same blocks produced two — so the check was live and the negative was real, not a dead code path.

The corpus does not follow the "parser-compatible JSON" reading.
Both fixtures carry human prose (`"Issue #42: Login button misaligned (open)"`) beside a `structuredContent` payload, as do the worked examples (`examples.md` ex§2) and the archived eval runs.
Enforcing JSON-parseability as the review proposed would have failed the skill's own conforming fixtures.

The spec's own position is a backwards-compatibility SHOULD: a tool returning `structuredContent` should also return the serialized JSON in a text block.
It does not forbid a prose block, and it does not make the serialized copy the only legal content.

## Decision

Keep both roles, distinguish them, and make agreement the binding requirement rather than encoding.

- `[3.content-types]` owns what fallback blocks must hold; `[3.output-schema]` points at it instead of stating a second, stricter rule.
- A human-rendering block is prose and is not required to parse as JSON. Reporting prose as a defect for being prose is a review error.
- A serialized copy of the structured payload is permitted and optional under this skill, per the spec's compatibility SHOULD.
- Binding: no `content` block may contradict `structuredContent`. A block parsing to a JSON object or array is read as the serialized copy and must equal the payload.

Rationale for making agreement the rule: two carriers giving different answers splits clients on which one they believe, which is strictly worse than an absent fallback. Encoding is a style choice; disagreement is a defect.

## Rejected

Requiring parser-compatible JSON in every `content` block, as the review proposed.
It contradicts `[3.content-types]`, fails both current fixtures and the worked examples, and mandates more than the spec asks.

Adding a new rule id for the fallback contract.
`[3.content-types]` is already its home, and the same review raised the checklist's volume as a cost — a new id would add to the count to hold a rule an existing id already owns.

## Enforcement

`tests/validate_fixture.py` checks agreement, not encoding: a JSON-object/array-parseable text block must equal `structuredContent`; prose passes; a scalar-parseable block ("42") stays prose so numeric summaries do not trip the check.
Equality is by JSON type, not Python's — `True == 1` in Python, so a `true` fallback would otherwise satisfy a `1` payload; numbers still compare numerically, so `1` and `1.0` agree.
The guarantee is scoped to the serialized half: whether a prose sentence contradicts the payload is not decidable from a fixture, so prose agreement stays a review obligation and a clean validator run is not evidence the prose agrees.
Both limits are stated in the rule and pinned by tests, so a future reader does not mistake the validator's silence for coverage.
Skipped where `structuredContent` is absent — the `[3.output-schema]` carve-out, and the disclosed degraded carrier where `content[0].text` *is* the envelope.
Four tests pin it, including the prose case, so a future tightening toward mandatory JSON fails a test that states why.
