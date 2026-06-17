"""Tests for the MCP wiring in datakit.server.

We assert the tools are registered and that calling them through the FastMCP
machinery returns the same answers as the underlying core functions, so the thin
wrapper layer is genuinely exercised.
"""

from __future__ import annotations

import asyncio

from datakit import server


def test_all_core_tools_are_registered() -> None:
    tools = asyncio.run(server.mcp.list_tools())
    names = {t.name for t in tools}
    expected = {
        "hash_text",
        "encode_base64",
        "decode_base64",
        "deterministic_uuid",
        "canonical_json",
        "json_diff",
        "convert_timezone",
        "add_duration",
        "time_between",
        "list_timezones",
    }
    assert expected <= names


def test_every_tool_has_a_description() -> None:
    tools = asyncio.run(server.mcp.list_tools())
    assert all(t.description for t in tools)


def test_call_tool_round_trips_through_fastmcp() -> None:
    result = asyncio.run(server.mcp.call_tool("hash_text", {"text": ""}))
    # call_tool returns (content_blocks, structured_result); assert the structured
    # value matches core's known empty-string SHA-256.
    structured = result[1]
    assert structured["result"] == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


def test_main_is_callable() -> None:
    # Smoke-check the entry point exists and is wired to mcp.run without invoking
    # the blocking stdio loop.
    assert callable(server.main)


def test_main_module_importable() -> None:
    # Importing the module entry point should not run the blocking loop.
    import importlib

    mod = importlib.import_module("datakit.__main__")
    assert hasattr(mod, "main")


def _call(name: str, args: dict):
    # FastMCP wraps scalar/list returns under {"result": ...} but returns dict
    # results directly when they match the tool's output schema. Normalize both.
    structured = asyncio.run(server.mcp.call_tool(name, args))[1]
    if isinstance(structured, dict) and set(structured.keys()) == {"result"}:
        return structured["result"]
    return structured


def test_each_tool_callable_through_fastmcp() -> None:
    # Exercise every registered wrapper so the thin server layer is fully covered
    # and the tool signatures are confirmed to accept their documented inputs.
    assert _call("encode_base64", {"text": "hi"}) == "aGk="
    assert _call("decode_base64", {"data": "aGk="}) == "hi"
    assert _call("deterministic_uuid", {"name": "a"}) == _call(
        "deterministic_uuid", {"name": "a"}
    )
    assert _call("canonical_json", {"value": {"b": 1, "a": 2}}) == '{"a":2,"b":1}'
    diff = _call("json_diff", {"left": {"a": 1}, "right": {"a": 2}})
    assert diff["changed"][0]["path"] == "a"
    assert _call(
        "convert_timezone",
        {"timestamp": "2026-06-01T00:00:00Z", "to_timezone": "UTC"},
    ) == "2026-06-01T00:00:00+00:00"
    assert _call(
        "add_duration", {"timestamp": "2026-01-01T00:00:00+00:00", "days": 1}
    ) == "2026-01-02T00:00:00+00:00"
    assert _call(
        "time_between",
        {"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-01T01:00:00+00:00"},
    )["hours"] == 1.0
    assert "UTC" in _call("list_timezones", {})
