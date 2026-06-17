# agent-mcp

The **public MCP (Model Context Protocol) marketplace-aggregator** for Selamy Labs —
the public counterpart to [`agent-skills`](https://github.com/selamy-labs/agent-skills).
It is the single discovery + distribution point for our public MCP servers. Each
server is **maintained in its own versioned repo** (per-server packaging); this repo
aggregates them, pinned by tag, as a Claude Code plugin marketplace.

Proprietary/internal MCP servers live in the private `internal-agent-mcp` repo.

## Why per-server repos + one aggregator

MCP servers, unlike markdown skills, **are software packages**. Each gets clean,
independent Python packaging, its own CI + coverage gate, its own semver tags, and
`uvx --from git+<repo>@<tag>` reproducible install — without the multi-package
versioning mess of a monorepo. This repo gives them a single home for discovery and
native, pinned distribution, so workloads add **one** marketplace instead of tracking
five repos. (Decision: `#606` / `#653` Option B.)

## Servers in the marketplace

Defined in [`mcp-servers.json`](./mcp-servers.json), each pinned to a release tag:

| Server | Repo | What it does |
|---|---|---|
| `laneq` | [selamy-labs/laneq](https://github.com/selamy-labs/laneq) | Local SQLite priority queue for feeding directives to agents |
| `reddit` | [selamy-labs/reddit-mcp](https://github.com/selamy-labs/reddit-mcp) | Terms-aware, read-only Reddit research as typed tools |
| `dispatch` | [selamy-labs/dispatch-mcp](https://github.com/selamy-labs/dispatch-mcp) | Security-constrained dispatch of work to allowlisted lanes |
| `memory` | [selamy-labs/memory-mcp](https://github.com/selamy-labs/memory-mcp) | Read/careful-write over the fleet markdown-memory store |
| `telemetry` | [selamy-labs/telemetry-mcp](https://github.com/selamy-labs/telemetry-mcp) | Read-only queries over a configurable metrics backend (BigQuery-ready) |

> `telemetry` is pinned to `@main` pending its first semver tag — see the open
> follow-up to cut `v0.1.0` and re-pin.

## Model

- **Public-first.** A server is public unless it must be private; the privacy
  scanner is the gate. This repo never references internal counterparts.
- **Quality bar.** Each per-server repo carries branch protection + required CI +
  privacy/secret scan + a >=90% coverage floor (matches the public-repo standard).
- **Versioned.** Servers are semver-tagged; the aggregator pins each by tag for
  reproducible, pinned consumption.
- **Distribution.** This repo is a Claude Code **plugin marketplace** for MCP
  servers (mirroring `agent-skills`), so workloads declare + pin natively rather
  than copying configs around.

## Adding a server

1. Build it in its own repo (`<name>-mcp`), Python-packaged, CI + coverage-gated,
   privacy-clean, semver-tagged. Internal/proprietary servers go in
   `internal-agent-mcp` instead.
2. Add an entry to `mcp-servers.json` pinned to a release tag.
3. CI here validates the manifests + secret-scans before merge.
