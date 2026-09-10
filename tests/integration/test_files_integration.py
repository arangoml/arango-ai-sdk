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
from arango_ai_sdk.files import FileManager

DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")
RAG_INPUT_PATH = f"{FileManagerPath.PREFIX}/{DB_NAME}/{FileManagerPath.RAG_INPUT}"


@pytest.fixture
def scope() -> list[str]:
    """Return a scope unique to this test, so parallel runs cannot collide."""
    return ["sdk_test", uuid.uuid4().hex[:8]]


@pytest.fixture
def files(communication: Communication, scope: list[str]) -> Iterator[FileManager]:
    """Build the namespace under test and delete everything it uploaded on exit."""
    manager = FileManager(communication, db_name=DB_NAME)
    yield manager
    # The listing filters by one label only, so narrow it to this test's scope
    # here, then delete whole lineages by id.
    listed = communication.send_request(
        "get", RAG_INPUT_PATH, params={"scope": scope[0], "limit": "1000"}
    )
    ids = []
    for stored in listed["files"]:
        stored_scope = stored.get("scope") or []
        if stored_scope[: len(scope)] == scope:
            ids.append(stored["id"])
    if ids:
        communication.send_request("post", f"{RAG_INPUT_PATH}/delete", data={"ids": ids})


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


def test_upload_files_reports_each_file_and_keeps_going_past_a_bad_one(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    good = tmp_path / "good.txt"
    good.write_text("good")
    empty = tmp_path / "empty.txt"
    empty.touch()

    results = files.upload_files([good, empty], scope=scope)

    stored, failed = results
    assert stored.ok and stored.name == "good.txt" and stored.scope == tuple(scope)
    assert stored.file is not None
    assert stored.file.id and stored.file.version == 1 and stored.file.database == DB_NAME
    assert not failed.ok and failed.file is None
    assert failed.name == "empty.txt" and "empty" in (failed.detail or "")


def test_upload_files_places_each_file_under_its_own_scope(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    legal = tmp_path / "nda.txt"
    legal.write_text("n")
    finance = tmp_path / "q1.txt"
    finance.write_text("q")

    results = files.upload_files({legal: [*scope, "legal"], finance: [*scope, "finance"]})

    assert all(result.ok for result in results)
    by_name = {result.name: result for result in results}
    assert by_name["nda.txt"].scope == (*scope, "legal")
    assert by_name["q1.txt"].scope == (*scope, "finance")


def test_upload_folder_takes_the_folder_files_and_ignores_subfolders(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    (tmp_path / "top.txt").write_text("t")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "deep.txt").write_text("d")

    results = files.upload_folder(tmp_path, scope=scope)

    (top,) = results
    assert top.ok and top.name == "top.txt" and top.scope == tuple(scope)
