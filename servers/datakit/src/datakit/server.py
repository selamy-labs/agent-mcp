"""datakit MCP server.

A thin FastMCP wrapper exposing the deterministic helpers in :mod:`datakit.core`
as typed MCP tools. Keeping all logic in ``core`` means the transport layer here
stays trivial and the behavior is fully unit-tested.

Run as a stdio MCP server:

    datakit-mcp            # console script (see pyproject)
    python -m datakit      # module entry point
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import core

mcp = FastMCP("datakit")


@mcp.tool()
def hash_text(text: str, algorithm: str = "sha256") -> str:
    """Hash UTF-8 text and return the hex digest.

    algorithm: one of sha256, sha512, sha1, md5 (default sha256).
    """
    return core.hash_text(text, algorithm)


@mcp.tool()
def encode_base64(text: str, urlsafe: bool = False) -> str:
    """Base64-encode UTF-8 text. Set urlsafe=true for the URL/filename alphabet."""
    return core.encode_base64(text, urlsafe)


@mcp.tool()
def decode_base64(data: str, urlsafe: bool = False) -> str:
    """Decode base64 text back to a UTF-8 string. Padding is optional."""
    return core.decode_base64(data, urlsafe)


@mcp.tool()
def deterministic_uuid(name: str, namespace: str | None = None) -> str:
    """Generate a stable UUIDv5 for a name. Same input always yields the same id.

    namespace: optional UUID string; defaults to the DNS namespace.
    """
    return core.deterministic_uuid(name, namespace)


@mcp.tool()
def canonical_json(value: Any, indent: int | None = None) -> str:
    """Serialize a JSON value canonically (sorted keys, stable separators).

    Equal objects always produce byte-identical output. Pass indent for a
    pretty-printed variant.
    """
    return core.canonical_json(value, indent)


@mcp.tool()
def json_diff(left: Any, right: Any) -> dict[str, list[dict[str, Any]]]:
    """Structurally diff two JSON values into added / removed / changed paths."""
    return core.json_diff(left, right)


@mcp.tool()
def convert_timezone(
    timestamp: str, to_timezone: str, from_timezone: str | None = None
) -> str:
    """Convert an ISO-8601 timestamp to another IANA timezone.

    Supply from_timezone if the timestamp has no offset.
    """
    return core.convert_timezone(timestamp, to_timezone, from_timezone)


@mcp.tool()
def add_duration(timestamp: str, seconds: int = 0, days: int = 0) -> str:
    """Add a signed duration (days and/or seconds) to an ISO-8601 timestamp."""
    return core.add_duration(timestamp, seconds, days)


@mcp.tool()
def time_between(start: str, end: str) -> dict[str, float]:
    """Compute the signed span from start to end in seconds/minutes/hours/days."""
    return core.time_between(start, end)


@mcp.tool()
def list_timezones(prefix: str = "") -> list[str]:
    """List IANA timezone names, optionally filtered by a case-insensitive prefix."""
    return core.list_timezones(prefix)


def main() -> None:
    """Console-script entry point: run the server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
