# datakit

A small, generic MCP server of **deterministic data utilities** — the operations
agents reach for constantly and that LLMs get subtly wrong when doing them "in
their head": byte-accurate encoding, cryptographic hashing, stable JSON
canonicalization, structural JSON diffing, and timezone-correct datetime math.

Every tool is pure and deterministic. There is no network access, no
authentication, and no state, so the server is safe to call freely from an agent
loop and trivially reproducible.

## Tools

| Tool | Purpose |
| --- | --- |
| `hash_text` | Hex digest of UTF-8 text (sha256 / sha512 / sha1 / md5). |
| `encode_base64` / `decode_base64` | Base64 round-trip, standard or URL-safe alphabet, padding optional on decode. |
| `deterministic_uuid` | Stable UUIDv5 for a name (idempotent keys); optional namespace. |
| `canonical_json` | Sorted-key, stable-separator JSON for hashing/signing/diffing. |
| `json_diff` | Structural added / removed / changed diff of two JSON values. |
| `convert_timezone` | Convert an ISO-8601 timestamp between IANA timezones. |
| `add_duration` | Add a signed days/seconds duration to a timestamp. |
| `time_between` | Signed span between two timestamps in seconds/minutes/hours/days. |
| `list_timezones` | IANA timezone names, optionally filtered by prefix. |

## Run

```bash
# from this directory
pip install -e ".[mcp]"
datakit-mcp            # stdio MCP server
# or
python -m datakit
```

### Claude Code / MCP client config

```json
{
  "mcpServers": {
    "datakit": {
      "command": "uvx",
      "args": [
        "--from",
        "datakit-mcp[mcp] @ git+https://github.com/selamy-labs/agent-mcp@main#subdirectory=servers/datakit",
        "datakit-mcp"
      ]
    }
  }
}
```

Pin `@main` to a release tag for reproducible installs.

## Develop

```bash
pip install -e ".[test]"
pytest        # runs with coverage, fails under 90%
```

## Layout

```
src/datakit/core.py     # pure, deterministic logic (fully unit-tested)
src/datakit/server.py   # thin FastMCP wrapper exposing core as typed tools
tests/                  # behavioral tests incl. error paths
```

The split keeps the transport layer trivial and the logic directly testable.

## License

MIT
