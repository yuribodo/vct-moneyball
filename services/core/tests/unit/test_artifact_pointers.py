"""T-new — LATEST pointer files: deterministic read/write, no mtime involved."""

from __future__ import annotations

from vct_moneyball.common.artifact_pointers import read_pointer, write_pointer


def test_read_missing_pointer_is_none(tmp_path) -> None:
    assert read_pointer(tmp_path / "LATEST") is None


def test_write_then_read_round_trips(tmp_path) -> None:
    pointer = tmp_path / "family" / "LATEST"
    write_pointer(pointer, "enc-2026.bridge.v3")
    assert read_pointer(pointer) == "enc-2026.bridge.v3"
    assert pointer.read_text() == "enc-2026.bridge.v3\n"


def test_write_overwrites_existing_pointer(tmp_path) -> None:
    pointer = tmp_path / "LATEST"
    write_pointer(pointer, "v1")
    write_pointer(pointer, "v2")
    assert read_pointer(pointer) == "v2"


def test_blank_pointer_file_is_none(tmp_path) -> None:
    pointer = tmp_path / "LATEST"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text("   \n")
    assert read_pointer(pointer) is None
