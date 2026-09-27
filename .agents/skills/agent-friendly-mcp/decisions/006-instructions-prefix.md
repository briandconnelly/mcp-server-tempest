# 006 — Server `instructions` delivered as a prefix

Decided 2026-09-26.
Triggered by issue #184, which reported that Claude Code delivers only a fixed-length prefix of a server's `instructions` string and proposed rules for laying the string out around that cut.

## Question

`[2.instructions-advisory]` covered a client that never surfaces `instructions`.
It did not cover a client that surfaces the head and drops the rest, which leaves the agent holding a plausible partial contract.
Which rules does that failure need, and should the skill state a length budget?

## Evidence

These are dated observations of client behavior, not protocol facts.
Each figure can change with a client release, and at least one is configurable per session.

| Client | Observation | Source |
| --- | --- | --- |
| Claude Code | First 2,048 characters of a 13.9 KB string reached the model, followed by a client-rendered `… [truncated]` marker; earlier readings on the same client landed near 2,041 bytes and 2,058 characters. | Issue #184, citing runpod/snowpod#463, #437, #299 (2026-09-26 and earlier) |
| Claude Code 2.1.283 | A fresh session's transcript records the injected block (an `mcp_instructions_delta` attachment): exactly the first 2,048 characters of amicus 0.7.0's 3,438-character instructions, matching the server's `manifest_snapshot.all.json` fixture, followed by `… [truncated]`. That prefix holds two em dashes, so it is 2,052 UTF-8 bytes: the cut is in characters, not bytes. The block arrived with the session's second message, when the slow-starting server finished connecting; on the first message neither amicus's tools nor its instructions were present, so the model said it saw none. `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` was unset in the authoring session, which saw the same 2,046 visible characters. | The maintainer's session `d7a2e144`, 2026-09-26, and this PR's authoring session, both read against the amicus fixture |
| Claude Code (changelog) | 2.1.280 "Added `CLAUDE_CODE_MAX_MCP_DESCRIPTION_LENGTH` to change the 2,048-character cap on MCP tool descriptions and server instructions for every MCP server in the session." The cap is a documented default the user can raise or lower, so a server cannot know the prefix a given Claude Code session delivers. | <https://code.claude.com/docs/en/changelog.md>, read 2026-09-26 |
| Codex CLI 0.157.1 | Codex carries the full `instructions` string inside the server's tool descriptions. In a VS Code-hosted session, amicus 0.6.0's 3,392-character (3,396-byte) string, byte-identical to its `initialize` result, heads a 6,030-character `amicus_backends` description, and the four amicus descriptions visible in a separate, truncated capture begin with the same text. No separate instructions text was reported: fresh `codex exec` sessions told not to use tools said they saw none, and one listing its tools listed no MCP tools. `codex exec` sessions prompted to find a tool definition recovered the whole string, including an 11,682-character ASCII probe (last sentinel and tail value correct); the transcripts do not show whether that text sat in starting tool metadata or arrived through an unlogged lookup. No cut was seen at these lengths, including none at 1,000 bytes for a plugin-declared server, and the lengths are lower bounds. A fresh VS Code-hosted TUI session told not to use tools also reported no amicus server instructions, only the amicus skill listing; its rollout shows no tool calls and does not contain the instructions text. Other Codex surfaces were not measured. | The maintainer's sessions and this PR's probes, 2026-09-26, read from the Codex session rollouts and debug log |
| Codex (docs) | "Keep the first 512 characters self-contained so the most important guidance is available when Codex is deciding how to use the server." No truncation limit is documented. | <https://learn.chatgpt.com/docs/extend/mcp?surface=cli> and <https://developers.openai.com/plugins/build/mcp-server>, read 2026-09-26 |

Issue #184 also reported a cold-start observation (runpod/snowpod#462): with a truncation self-test at the head, the agent followed the rules inside the prefix and went straight to the resource it needed, without acting on the self-test.

## Decision

Add two rules and extend one.

- `[2.instructions-advisory]` names the prefix case and the tool-definition case (Codex CLI above) alongside the never-surfaced case, so all three route to the same "never the sole carrier" requirement.
- `[2.instructions-prefix]` owns the layout and the length budget.
- `[2.truncation-signal]` owns the self-check the agent can run on its own copy, and why it is a floor (the cold-start observation above).
- `review-workflow.md` gains a measurement step in the cold-start probe and a Major example for binding rules past a measured prefix.

The rules state no number.
The two measured clients fail differently: Claude Code cuts at a user-adjustable 2,048 characters, while Codex CLI carried at least 5.7× that uncut, inside tool definitions rather than as separate context.
The documented Codex figure is guidance rather than a limit.
A skill meant for many clients would be wrong for most of them if it bound one client's figure.
The figures live in this record so a reader can see where a budget came from and when it was last measured.

## Rejected

A fixed 2,048-character budget in the rule, as issue #184 proposed.
It is one client's current behavior; applied to Codex CLI it would cap a server's usable text at under a fifth of what that path carries in its tool definitions, and it is not stable even within Claude Code, where a session can change it.

A separate rule for digests over glossaries (issue #184's proposed `2.instructions-digest-not-glossary`).
It is one consequence of ordering by what the agent needs first, so it lives as a sentence in `[2.instructions-prefix]` rather than as a third rule with its own id.

Measuring in both characters and UTF-8 bytes until the unit is known, as the issue proposed.
The Claude Code measurement above settles the unit for that client, and the rule already asks for the unit each target client cuts in, which covers clients whose unit is still unknown.
