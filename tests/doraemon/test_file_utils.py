"""Tests for :mod:`doraemon.file_utils`."""

from __future__ import annotations

from pathlib import Path

import pytest

from doraemon.file_utils import find_all_filepaths


def test_find_all_filepaths_finds_csvs(tmp_path: Path):
    (tmp_path / "a.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    (tmp_path / "b.csv").write_text("x,y\n3,4\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.csv").write_text("x\n1\n", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("nope", encoding="utf-8")

    paths = find_all_filepaths(str(tmp_path), "csv")

    assert len(paths) == 3
    assert all(p.endswith(".csv") for p in paths)


def test_find_all_filepaths_returns_empty_when_no_match(tmp_path: Path):
    (tmp_path / "only.txt").write_text("hello", encoding="utf-8")
    assert find_all_filepaths(str(tmp_path), "csv") == []


@pytest.mark.parametrize("filetype", ["csv", "xlsx", "numbers"])
def test_find_all_filepaths_filters_by_extension(tmp_path: Path, filetype: str):
    (tmp_path / f"x.{filetype}").write_text("data", encoding="utf-8")
    (tmp_path / "y.other").write_text("data", encoding="utf-8")

    found = find_all_filepaths(str(tmp_path), filetype)

    assert len(found) == 1
    assert found[0].endswith(f".{filetype}")
