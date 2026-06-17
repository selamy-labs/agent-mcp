"""Behavioral tests for datakit.core.

These assert real, externally-checkable values (known digests, round-trips,
timezone-correct conversions) rather than restating the implementation, and they
cover the error paths that give the agent its safety guarantees.
"""

from __future__ import annotations

import hashlib
import uuid

import pytest

from datakit import core
from datakit.core import DataKitError


# --- hashing ---------------------------------------------------------------

def test_hash_text_sha256_known_value() -> None:
    # Empty-string SHA-256 is a well-known fixed digest.
    assert core.hash_text("") == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


@pytest.mark.parametrize("algo", ["sha256", "sha512", "sha1", "md5"])
def test_hash_text_matches_hashlib(algo: str) -> None:
    expected = hashlib.new(algo, b"hello").hexdigest()
    assert core.hash_text("hello", algo) == expected


def test_hash_text_is_case_insensitive_on_algorithm() -> None:
    assert core.hash_text("x", "SHA256") == core.hash_text("x", "sha256")


def test_hash_text_rejects_unknown_algorithm() -> None:
    with pytest.raises(DataKitError, match="unsupported algorithm"):
        core.hash_text("x", "crc32")


# --- base64 ----------------------------------------------------------------

def test_base64_round_trip_unicode() -> None:
    text = "héllo, 世界"
    assert core.decode_base64(core.encode_base64(text)) == text


def test_base64_urlsafe_alphabet() -> None:
    # This string's UTF-8 base64 contains a "/" in the standard alphabet, which
    # the URL-safe alphabet renders as "_" -- so the two encodings must differ.
    text = "\x8f\x8f\x8f"
    std = core.encode_base64(text)
    url = core.encode_base64(text, urlsafe=True)
    assert "/" in std and "/" not in url
    assert std != url
    assert core.decode_base64(url, urlsafe=True) == text


def test_decode_base64_accepts_missing_padding() -> None:
    # "any" -> "YW55" has no padding; "anyx" needs padding.
    encoded = core.encode_base64("anyx").rstrip("=")
    assert core.decode_base64(encoded) == "anyx"


def test_decode_base64_rejects_garbage() -> None:
    with pytest.raises(DataKitError, match="invalid base64"):
        core.decode_base64("!!!not base64!!!")


def test_decode_base64_rejects_non_utf8() -> None:
    import base64 as _b64

    bad = _b64.b64encode(b"\xff\xfe").decode("ascii")
    with pytest.raises(DataKitError, match="not valid UTF-8"):
        core.decode_base64(bad)


# --- deterministic uuid ----------------------------------------------------

def test_deterministic_uuid_is_stable() -> None:
    assert core.deterministic_uuid("order-42") == core.deterministic_uuid("order-42")


def test_deterministic_uuid_matches_uuid5() -> None:
    assert core.deterministic_uuid("example.com") == str(
        uuid.uuid5(uuid.NAMESPACE_DNS, "example.com")
    )


def test_deterministic_uuid_namespace_changes_output() -> None:
    other_ns = str(uuid.uuid4())
    assert core.deterministic_uuid("a", other_ns) != core.deterministic_uuid("a")


def test_deterministic_uuid_rejects_bad_namespace() -> None:
    with pytest.raises(DataKitError, match="valid UUID"):
        core.deterministic_uuid("a", "not-a-uuid")


# --- canonical json --------------------------------------------------------

def test_canonical_json_is_order_independent() -> None:
    a = core.canonical_json({"b": 1, "a": 2})
    b = core.canonical_json({"a": 2, "b": 1})
    assert a == b == '{"a":2,"b":1}'


def test_canonical_json_preserves_unicode() -> None:
    assert core.canonical_json({"k": "世"}) == '{"k":"世"}'


def test_canonical_json_indent() -> None:
    out = core.canonical_json({"a": 1}, indent=2)
    assert out == '{\n  "a": 1\n}'


# --- json diff -------------------------------------------------------------

def test_json_diff_detects_all_change_kinds() -> None:
    left = {"keep": 1, "drop": 2, "change": 3, "nest": {"x": 1}}
    right = {"keep": 1, "add": 9, "change": 4, "nest": {"x": 1}}
    diff = core.json_diff(left, right)
    assert diff["added"] == [{"path": "add", "value": 9}]
    assert diff["removed"] == [{"path": "drop", "value": 2}]
    assert diff["changed"] == [{"path": "change", "from": 3, "to": 4}]


def test_json_diff_handles_lists() -> None:
    diff = core.json_diff({"xs": [1, 2]}, {"xs": [1, 3, 4]})
    paths = {c["path"] for c in diff["changed"]}
    added = {a["path"] for a in diff["added"]}
    assert "xs[1]" in paths
    assert "xs[2]" in added


def test_json_diff_identical_is_empty() -> None:
    same = {"a": [1, {"b": 2}]}
    assert core.json_diff(same, same) == {"added": [], "removed": [], "changed": []}


# --- timezone / datetime ---------------------------------------------------

def test_convert_timezone_aware_input() -> None:
    out = core.convert_timezone("2026-01-01T12:00:00+00:00", "America/New_York")
    # NY is UTC-5 in January (standard time).
    assert out == "2026-01-01T07:00:00-05:00"


def test_convert_timezone_accepts_z_suffix() -> None:
    out = core.convert_timezone("2026-06-01T00:00:00Z", "UTC")
    assert out == "2026-06-01T00:00:00+00:00"


def test_convert_timezone_naive_requires_source() -> None:
    with pytest.raises(DataKitError, match="from_timezone"):
        core.convert_timezone("2026-01-01T00:00:00", "UTC")


def test_convert_timezone_naive_with_source() -> None:
    out = core.convert_timezone(
        "2026-01-01T00:00:00", "UTC", from_timezone="America/New_York"
    )
    assert out == "2026-01-01T05:00:00+00:00"


def test_convert_timezone_unknown_zone() -> None:
    with pytest.raises(DataKitError, match="unknown timezone"):
        core.convert_timezone("2026-01-01T00:00:00Z", "Mars/Olympus")


def test_convert_timezone_bad_timestamp() -> None:
    with pytest.raises(DataKitError, match="invalid ISO-8601"):
        core.convert_timezone("not-a-date", "UTC")


def test_add_duration_days_and_seconds() -> None:
    assert core.add_duration("2026-01-01T00:00:00+00:00", days=1, seconds=3600) == (
        "2026-01-02T01:00:00+00:00"
    )


def test_add_duration_negative() -> None:
    assert core.add_duration("2026-01-02T00:00:00+00:00", days=-1) == (
        "2026-01-01T00:00:00+00:00"
    )


def test_time_between_units() -> None:
    out = core.time_between(
        "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"
    )
    assert out == {"seconds": 86400.0, "minutes": 1440.0, "hours": 24.0, "days": 1.0}


def test_time_between_is_signed() -> None:
    out = core.time_between(
        "2026-01-02T00:00:00+00:00", "2026-01-01T00:00:00+00:00"
    )
    assert out["seconds"] == -86400.0


def test_time_between_rejects_mixed_awareness() -> None:
    with pytest.raises(DataKitError, match="naive timestamp with an aware"):
        core.time_between("2026-01-01T00:00:00", "2026-01-02T00:00:00+00:00")


def test_list_timezones_prefix_filter() -> None:
    zones = core.list_timezones("america/")
    assert "America/New_York" in zones
    assert all(z.lower().startswith("america/") for z in zones)


def test_list_timezones_unfiltered_nonempty_sorted() -> None:
    zones = core.list_timezones()
    assert "UTC" in zones
    assert zones == sorted(zones)
