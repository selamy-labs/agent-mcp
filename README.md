# agent-mcp

Canonical home for **public, generic MCP (Model Context Protocol) servers** built
by Selamy Labs for autonomous agents — the public counterpart to
[`agent-skills`](https://github.com/selamy-labs/agent-skills). Proprietary/internal
MCP servers live in the private `internal-agent-mcp` repo.

## Why this repo

MCP servers give agents typed, reusable tool integrations. Publishing the generic
ones openly is a differentiator and a free-marketing flywheel — the same model that
governs our public skills. The bar is high on purpose: only genuinely useful,
well-tested servers ship here. Slop dilutes the brand.

## Model

- **Public-first.** A server is public unless it must be private; the privacy
  scanner is the gate. This repo never references internal counterparts.
- **Quality bar.** Branch protection + required CI + privacy/secret scan + a >=90%
  coverage floor for anything that ships (matches the public-repo standard).
- **Versioned.** Servers are semver-tagged for reproducible, pinned consumption.
- **Distribution.** This repo can double as a Claude Code **plugin marketplace** for
  MCP servers (mirroring `agent-skills`), so workloads declare + pin them natively
  rather than copying configs around.

## Layout (planned)

```
servers/<server-name>/   # one MCP server per directory
.claude-plugin/          # marketplace.json + plugin.json (MCP marketplace)
```

## Contributing

A server must be generic (not Selamy-internal), privacy-clean, tested to the
coverage floor, and documented. CI enforces the gates before merge. Internal or
proprietary servers belong in `internal-agent-mcp`.

> Status: repo bootstrapped via IaC (#606). CI + privacy-scanner + the first
> servers land next.
