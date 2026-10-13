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
from arango_ai_sdk.resources.files import FileManager

DB_NAME = os.environ.get(EnvVar.ARANGO_SDK_TEST_DB, "")
RAG_INPUT_PATH = f"{FileManagerPath.PREFIX}/{DB_NAME}/{FileManagerPath.RAG_INPUT}"


@pytest.fixture
def scope() -> list[str]:
    """Return a scope unique to this test, so parallel runs cannot collide."""
    return ["sdk_test", uuid.uuid4().hex[:8]]


@pytest.fixture
def files(
    file_manager_ready: None, communication: Communication, scope: list[str]
) -> Iterator[FileManager]:
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
    path.write_bytes(b"hello\n")

    first = files.upload_file(path, scope=scope, custom_metadata={"author": "sdk tests"})
    path.write_bytes(b"hello again\n")
    second = files.upload_file(path, scope=scope)

    assert first.name == "hello.txt"
    assert first.scope == scope
    assert first.database == DB_NAME
    assert first.version == 1 and first.safe_to_delete is True
    assert first.metadata_key and first.uploaded_at.tzinfo is not None
    assert first.custom_metadata == {"author": "sdk tests"}
    assert second.id == first.id and second.version == 2
    assert second.size == path.stat().st_size


def test_upload_files_places_each_file_under_its_own_scope_and_reports_what_the_platform_rejected(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    """A mapping's scopes win over ``scope``; a file the platform rejects stops nothing else."""
    legal = tmp_path / "nda.txt"
    legal.write_text("n")
    finance = tmp_path / "q1.txt"
    finance.write_text("q")
    empty = tmp_path / "empty.txt"
    empty.touch()

    results = files.upload_files(
        {legal: [*scope, "legal"], finance: [*scope, "finance"], empty: scope},
        scope=[*scope, "ignored"],
    )

    by_name = {result.name: result for result in results}
    assert by_name["nda.txt"].status == "ok" and by_name["nda.txt"].scope == [*scope, "legal"]
    assert by_name["q1.txt"].status == "ok" and by_name["q1.txt"].scope == [*scope, "finance"]
    rejected = by_name["empty.txt"]
    assert rejected.status == "error" and rejected.id is None
    assert "empty" in (rejected.detail or "")


def test_upload_files_uploads_a_path_listed_twice_as_two_versions(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    path = tmp_path / "hello.txt"
    path.write_text("hello")

    results = files.upload_files([path, path], scope=scope)

    first, second = results
    assert first.status == second.status == "ok"
    assert first.id == second.id
    assert (first.version, second.version) == (1, 2)


def test_upload_files_puts_the_same_file_under_two_scopes_as_two_lineages(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    """The platform versions by scope and name, so the same file under two scopes is two files.

    One call takes one scope per path, so this needs two calls.
    """
    path = tmp_path / "hello.txt"
    path.write_text("hello")

    (legal,) = files.upload_files({path: [*scope, "legal"]})
    (finance,) = files.upload_files({path: [*scope, "finance"]})

    assert legal.status == finance.status == "ok"
    assert legal.id != finance.id
    assert (legal.version, finance.version) == (1, 1)


def test_upload_folder_takes_the_folder_files_and_ignores_subfolders(
    files: FileManager, scope: list[str], tmp_path: Path
) -> None:
    (tmp_path / "top.txt").write_text("t")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "deep.txt").write_text("d")

    results = files.upload_folder(tmp_path, scope=scope)

    assert len(results) == 1
    (top,) = results
    assert top.status == "ok" and top.name == "top.txt" and top.scope == scope
