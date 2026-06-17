"""Pure, deterministic data utilities.

Every function here is side-effect free and deterministic, which makes the tools
safe to call from an agent loop and trivial to test. The MCP layer (``server.py``)
is a thin wrapper over these functions, so the logic is exercised directly by the
test suite without spinning up a transport.

These are exactly the operations LLMs are unreliable at when done "by hand":
byte-accurate encoding, cryptographic hashing, stable JSON canonicalization,
structural diffing, and timezone-correct datetime math. Exposing them as typed
tools removes a whole class of silent agent errors.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, available_timezones

# Algorithms we are willing to expose. Restricting the set keeps the public
# surface small and avoids leaking platform-dependent or insecure digests.
_HASH_ALGORITHMS = ("sha256", "sha512", "sha1", "md5")

# Fixed, well-known DNS namespace for deterministic UUIDv5 generation. Using a
# constant namespace by default means the same name always maps to the same id.
_DEFAULT_UUID_NAMESPACE = uuid.NAMESPACE_DNS


class DataKitError(ValueError):
    """Raised for invalid input. Maps cleanly to a tool-level error message."""


def hash_text(text: str, algorithm: str = "sha256") -> str:
    """Return the hex digest of ``text`` (UTF-8 encoded) under ``algorithm``."""
    algo = algorithm.lower()
    if algo not in _HASH_ALGORITHMS:
        raise DataKitError(
            f"unsupported algorithm {algorithm!r}; choose one of {', '.join(_HASH_ALGORITHMS)}"
        )
    digest = hashlib.new(algo)
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def encode_base64(text: str, urlsafe: bool = False) -> str:
    """Base64-encode UTF-8 ``text``. ``urlsafe`` selects the URL/filename alphabet."""
    raw = text.encode("utf-8")
    encoder = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    return encoder(raw).decode("ascii")


def decode_base64(data: str, urlsafe: bool = False) -> str:
    """Decode base64 ``data`` back to a UTF-8 string.

    Accepts input with or without padding; raises :class:`DataKitError` on
    malformed base64 or non-UTF-8 payloads so the agent gets a clear signal.
    """
    padded = data + "=" * (-len(data) % 4)
    decoder = base64.urlsafe_b64decode if urlsafe else base64.b64decode
    try:
        raw = decoder(padded)
    except (binascii.Error, ValueError) as exc:
        raise DataKitError(f"invalid base64 input: {exc}") from exc
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DataKitError("decoded bytes are not valid UTF-8") from exc


def deterministic_uuid(name: str, namespace: str | None = None) -> str:
    """Return a stable UUIDv5 for ``name``.

    ``namespace`` is an optional UUID string used as the namespace; when omitted
    the DNS namespace is used. The same ``(namespace, name)`` pair always yields
    the same id, which is what makes this useful for idempotent keys.
    """
    if namespace is None:
        ns = _DEFAULT_UUID_NAMESPACE
    else:
        try:
            ns = uuid.UUID(namespace)
        except ValueError as exc:
            raise DataKitError(f"namespace must be a valid UUID: {exc}") from exc
    return str(uuid.uuid5(ns, name))


def canonical_json(value: Any, indent: int | None = None) -> str:
    """Serialize ``value`` to canonical JSON (sorted keys, stable separators).

    Two semantically equal objects always produce byte-identical output, which is
    what you want for hashing, signing, or diffing JSON.
    """
    separators = (",", ":") if indent is None else (",", ": ")
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=separators,
        indent=indent,
    )


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten nested dict/list structures into ``path -> leaf-value`` pairs."""
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in value:
            child = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(value[key], child))
        return out
    if isinstance(value, list):
        out = {}
        for index, item in enumerate(value):
            child = f"{prefix}[{index}]"
            out.update(_flatten(item, child))
        return out
    return {prefix or "": value}


def json_diff(left: Any, right: Any) -> dict[str, list[dict[str, Any]]]:
    """Structurally diff two JSON-compatible values.

    Returns a dict with ``added``, ``removed``, and ``changed`` lists keyed by a
    dotted/bracketed path. This is deterministic and far more reliable than asking
    a model to eyeball two blobs.
    """
    left_flat = _flatten(left)
    right_flat = _flatten(right)
    left_keys = set(left_flat)
    right_keys = set(right_flat)

    added = [
        {"path": path, "value": right_flat[path]}
        for path in sorted(right_keys - left_keys)
    ]
    removed = [
        {"path": path, "value": left_flat[path]}
        for path in sorted(left_keys - right_keys)
    ]
    changed = [
        {"path": path, "from": left_flat[path], "to": right_flat[path]}
        for path in sorted(left_keys & right_keys)
        if left_flat[path] != right_flat[path]
    ]
    return {"added": added, "removed": removed, "changed": changed}


def convert_timezone(
    timestamp: str, to_timezone: str, from_timezone: str | None = None
) -> str:
    """Convert an ISO-8601 ``timestamp`` into ``to_timezone``.

    If the timestamp is naive (no offset) you must supply ``from_timezone``.
    Returns an ISO-8601 string carrying the target offset.
    """
    parsed = _parse_iso(timestamp)
    if parsed.tzinfo is None:
        if from_timezone is None:
            raise DataKitError(
                "naive timestamp requires from_timezone to be specified"
            )
        parsed = parsed.replace(tzinfo=_zone(from_timezone))
    return parsed.astimezone(_zone(to_timezone)).isoformat()


def add_duration(timestamp: str, seconds: int = 0, days: int = 0) -> str:
    """Add ``days`` and ``seconds`` (either may be negative) to ``timestamp``."""
    parsed = _parse_iso(timestamp)
    return (parsed + timedelta(days=days, seconds=seconds)).isoformat()


def time_between(start: str, end: str) -> dict[str, float]:
    """Return the signed span from ``start`` to ``end`` in several units.

    Both timestamps must be timezone-aware (or both naive); mixing the two is an
    error because the result would be ambiguous.
    """
    start_dt = _parse_iso(start)
    end_dt = _parse_iso(end)
    if (start_dt.tzinfo is None) != (end_dt.tzinfo is None):
        raise DataKitError("cannot compare a naive timestamp with an aware one")
    total = (end_dt - start_dt).total_seconds()
    return {
        "seconds": total,
        "minutes": total / 60,
        "hours": total / 3600,
        "days": total / 86400,
    }


def list_timezones(prefix: str = "") -> list[str]:
    """Return sorted IANA timezone names, optionally filtered by ``prefix``."""
    names = available_timezones()
    if prefix:
        names = {n for n in names if n.lower().startswith(prefix.lower())}
    return sorted(names)


def _parse_iso(timestamp: str) -> datetime:
    """Parse an ISO-8601 string, accepting a trailing ``Z`` for UTC."""
    text = timestamp.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise DataKitError(f"invalid ISO-8601 timestamp: {exc}") from exc


def _zone(name: str) -> timezone | ZoneInfo:
    """Resolve a timezone name to a tzinfo, accepting ``UTC`` explicitly."""
    if name.upper() == "UTC":
        return timezone.utc
    try:
        return ZoneInfo(name)
    except Exception as exc:  # noqa: BLE001 - normalize to a clear tool error
        raise DataKitError(f"unknown timezone {name!r}: {exc}") from exc
