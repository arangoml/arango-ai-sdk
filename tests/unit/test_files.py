"""Unit tests for :class:`FileManager`: what is refused before anything is sent.

The manager is built over a placeholder instead of a real ``Communication``.
Every call here must fail on a local check, so the placeholder is never used;
if the code did try to send, the test would fail with an ``AttributeError``.
"""

from pathlib import Path
from typing import cast

import pytest

from arango_ai_sdk import files
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import BatchTooLargeError, EmptyFileError, InvalidScopeError
from arango_ai_sdk.files import FileManager


@pytest.fixture
def manager() -> FileManager:
    return FileManager(cast(Communication, object()), db_name="sdk_test")


@pytest.fixture
def text_file(tmp_path: Path) -> Path:
    path = tmp_path / "hello.txt"
    path.write_text("hello")
    return path


# --------------------------------------------------------------------------- upload


@pytest.mark.parametrize(
    "scope",
    [
        ["a", "b", "c", "d", "e", "f"],  # more than five labels
        ["has space"],  # characters outside the allowed set
        [""],  # empty label
        ["x" * 129],  # label too long
        ["x" * 128, "y" * 128, "z"],  # combined length over 256
        ["acme\n"],  # a trailing newline must not slip past the pattern
    ],
)
def test_upload_refuses_a_bad_scope(manager: FileManager, text_file: Path, scope) -> None:
    with pytest.raises(InvalidScopeError) as excinfo:
        manager.upload(text_file, scope=scope)

    assert excinfo.value.status_code == 400


def test_upload_refuses_a_scope_given_as_a_string(manager: FileManager, text_file: Path) -> None:
    """A string is a ``Sequence[str]`` to the type checker; only a runtime check catches it."""
    with pytest.raises(InvalidScopeError, match="not a string"):
        manager.upload(text_file, scope="legal")


def test_upload_refuses_an_empty_file(manager: FileManager, tmp_path: Path) -> None:
    empty = tmp_path / "empty.txt"
    empty.touch()

    with pytest.raises(EmptyFileError) as excinfo:
        manager.upload(empty)

    assert excinfo.value.status_code == 422


def test_upload_refuses_a_folder_or_a_missing_path(manager: FileManager, tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError):
        manager.upload(tmp_path)
    with pytest.raises(FileNotFoundError):
        manager.upload(tmp_path / "missing.txt")


# --------------------------------------------------------------------------- upload_files


def test_upload_files_refuses_an_empty_list(manager: FileManager) -> None:
    with pytest.raises(ValueError, match="no files"):
        manager.upload_files([])


def test_upload_files_refuses_a_scope_given_both_ways(
    manager: FileManager, text_file: Path
) -> None:
    with pytest.raises(ValueError, match="not both"):
        manager.upload_files({text_file: ["acme"]}, scope=["acme"])


def test_upload_files_refuses_a_bad_scope_in_the_mapping(
    manager: FileManager, text_file: Path
) -> None:
    with pytest.raises(InvalidScopeError):
        manager.upload_files({text_file: ["not allowed!"]})


def test_upload_files_refuses_a_missing_path(manager: FileManager, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        manager.upload_files([tmp_path / "missing.txt"])


def test_upload_files_refuses_more_files_than_one_request_carries(
    manager: FileManager, tmp_path: Path
) -> None:
    paths = []
    for index in range(files.BATCH_MAX_FILES + 1):
        path = tmp_path / f"f{index}.txt"
        path.write_text("x")
        paths.append(path)

    with pytest.raises(BatchTooLargeError) as excinfo:
        manager.upload_files(paths)

    assert excinfo.value.status_code == 400


def test_upload_files_refuses_more_bytes_than_one_request_carries(
    manager: FileManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(files, "BATCH_MAX_BYTES", 10)
    first = tmp_path / "a.txt"
    first.write_bytes(b"x" * 6)
    second = tmp_path / "b.txt"
    second.write_bytes(b"x" * 6)

    with pytest.raises(BatchTooLargeError) as excinfo:
        manager.upload_files([first, second])

    assert excinfo.value.status_code == 413


# --------------------------------------------------------------------------- upload_folder


def test_upload_folder_refuses_a_missing_path_or_a_file(
    manager: FileManager, text_file: Path
) -> None:
    with pytest.raises(NotADirectoryError):
        manager.upload_folder(text_file.parent / "missing")
    with pytest.raises(NotADirectoryError):
        manager.upload_folder(text_file)


def test_upload_folder_refuses_an_empty_folder(manager: FileManager, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no files"):
        manager.upload_folder(tmp_path)


def test_upload_folder_ignores_subfolders(manager: FileManager, tmp_path: Path) -> None:
    """A folder whose only files sit in a subfolder holds no files to upload."""
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "deep.txt").write_text("d")

    with pytest.raises(ValueError, match="no files"):
        manager.upload_folder(tmp_path)
