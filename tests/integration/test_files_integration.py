"""Integration tests for :class:`FileManager`, against a live platform.

Marker and credentials skip come from ``tests/integration/conftest.py``. Every
test uploads under a scope unique to the run and deletes what it stored, also
when an assertion fails, so nothing accumulates on the shared deployment.
"""

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

from arango_ai_sdk._naming import EnvVar, FileManagerPath
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import EmptyFileError, InvalidScopeError
from arango_ai_sdk.files import FileManager

DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")


@pytest.fixture
def scope() -> list[str]:
    """Return a scope unique to this test, so parallel runs cannot collide."""
    return ["sdk_test", uuid.uuid4().hex[:8]]


@pytest.fixture
def files(communication: Communication, scope: list[str]) -> Iterator[FileManager]:
    """Build the namespace under test and delete everything it uploaded on exit."""
    manager = FileManager(communication, db_name=DB_NAME)
    yield manager
    # Delete whole lineages by id, a hundred per call. The listing filters by
    # the shared first label only, so narrow it to this test's scope here.
    listed = communication.send_request(
        "get", FileManagerPath.rag_input(DB_NAME), params={"scope": scope[0], "limit": "1000"}
    )
    ids = [f["id"] for f in listed["files"] if (f.get("scope") or [])[: len(scope)] == scope]
    for start in range(0, len(ids), 100):
        communication.send_request(
            "post",
            f"{FileManagerPath.rag_input(DB_NAME)}/delete",
            data={"ids": ids[start : start + 100]},
        )


def test_upload_stores_a_file_and_a_second_upload_makes_a_new_version(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    path = tmp_path / "hello.txt"
    path.write_text("hello\n")

    first = files.upload(path, scope=scope, custom_metadata={"author": "sdk tests"})
    path.write_text("hello again\n")
    second = files.upload(path, scope=scope)

    assert first.name == "hello.txt"
    assert first.scope == tuple(scope)
    assert first.database == DB_NAME
    assert first.version == 1 and first.safe_to_delete is True
    assert first.metadata_key and first.uploaded_at.tzinfo is not None
    assert first.custom_metadata == {"author": "sdk tests"}
    assert second.id == first.id and second.version == 2
    assert second.size == len("hello again\n")


def test_upload_many_reports_each_file_and_keeps_going_past_a_bad_one(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    good = tmp_path / "good.txt"
    good.write_text("good")
    empty = tmp_path / "empty.txt"
    empty.touch()

    result = files.upload_many([good, empty], scope=scope)

    assert (result.ok_count, result.error_count) == (1, 1)
    stored, failed = result.results
    assert stored.ok and stored.name == "good.txt" and stored.id and stored.version == 1
    assert not failed.ok and failed.name == "empty.txt" and "empty" in (failed.detail or "")


def test_upload_folder_keeps_the_folder_structure_as_scope_labels(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    (tmp_path / "top.txt").write_text("t")
    (tmp_path / "legal").mkdir()
    (tmp_path / "legal" / "nda.txt").write_text("n")

    result = files.upload_folder(tmp_path, scope=scope, preserve_paths=True)

    assert result.error_count == 0
    by_name = {r.name: r for r in result.results}
    assert by_name["top.txt"].scope == tuple(scope)
    assert by_name["nda.txt"].scope == (*scope, "legal")


def test_a_bad_scope_is_refused_before_anything_is_sent(files: FileManager, tmp_path: Path) -> None:
    path = tmp_path / "x.txt"
    path.write_text("x")

    with pytest.raises(InvalidScopeError):
        files.upload(path, scope=["not allowed!"])


def test_an_empty_file_is_refused_before_anything_is_sent(
    files: FileManager, tmp_path: Path
) -> None:
    path = tmp_path / "empty.txt"
    path.touch()

    with pytest.raises(EmptyFileError):
        files.upload(path)
