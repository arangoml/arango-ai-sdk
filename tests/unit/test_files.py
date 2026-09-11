"""Unit tests for :class:`FileManager` and its helpers: what is refused before sending.

The manager is built over a placeholder instead of a real ``Communication``.
Every call here must fail on a local check, so the placeholder is never used;
if the code did try to send, the test would fail with an ``AttributeError``.
What reaches the platform is covered by the integration tests.
"""

from pathlib import Path
from typing import cast

import pytest

from arango_ai_sdk import files
from arango_ai_sdk.communication import Communication
from arango_ai_sdk.exceptions import (
    EmptyFileError,
    FileBatchTooLargeError,
    FileUploadFailedError,
    InvalidFileMetadataError,
    InvalidFileScopeError,
    ServiceError,
)
from arango_ai_sdk.files import FileManager

RAG_INPUT = "/_platform/filemanager/_db/{database}/rag-input"


@pytest.fixture
def manager() -> FileManager:
    return FileManager(cast(Communication, object()), db_name="sdk_test")


def _service_error(status: int, detail: str, database: str = "sdk_test") -> ServiceError:
    """Build an error answer as ``Communication`` formats it: request line, then the detail."""
    path = RAG_INPUT.format(database=database)
    return ServiceError(f"POST {path} failed with {status}: {detail}", status_code=status)


@pytest.fixture
def text_file(tmp_path: Path) -> Path:
    path = tmp_path / "hello.txt"
    path.write_text("hello")
    return path


# --------------------------------------------------------------------------- upload_file


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
def test_upload_file_refuses_a_bad_scope(manager: FileManager, text_file: Path, scope) -> None:
    with pytest.raises(InvalidFileScopeError) as excinfo:
        manager.upload_file(text_file, scope=scope)

    assert excinfo.value.status_code == 400


def test_upload_file_refuses_a_scope_given_as_a_string(
    manager: FileManager, text_file: Path
) -> None:
    """A string is a ``Sequence[str]`` to the type checker; only a runtime check catches it."""
    with pytest.raises(InvalidFileScopeError, match="not a string"):
        manager.upload_file(text_file, scope="legal")


def test_upload_file_refuses_an_empty_file(manager: FileManager, tmp_path: Path) -> None:
    empty = tmp_path / "empty.txt"
    empty.touch()

    with pytest.raises(EmptyFileError) as excinfo:
        manager.upload_file(empty)

    assert excinfo.value.status_code == 422


def test_upload_file_refuses_a_folder_or_a_missing_path(
    manager: FileManager, tmp_path: Path
) -> None:
    with pytest.raises(IsADirectoryError):
        manager.upload_file(tmp_path)
    with pytest.raises(FileNotFoundError):
        manager.upload_file(tmp_path / "missing.txt")


# --------------------------------------------------------------------------- upload_files


def test_upload_files_refuses_an_empty_list(manager: FileManager) -> None:
    with pytest.raises(ValueError, match="no files"):
        manager.upload_files([])


@pytest.mark.parametrize("give", ["list", "mapping"])
def test_upload_files_refuses_a_scope_given_as_a_string(
    manager: FileManager, text_file: Path, give: str
) -> None:
    """The string guard applies to both ways of giving the scope."""
    with pytest.raises(InvalidFileScopeError, match="not a string"):
        if give == "list":
            manager.upload_files([text_file], scope="legal")
        else:
            manager.upload_files({text_file: "legal"})


def test_upload_files_refuses_a_bad_scope_in_the_mapping(
    manager: FileManager, text_file: Path
) -> None:
    with pytest.raises(InvalidFileScopeError):
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

    with pytest.raises(FileBatchTooLargeError) as excinfo:
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

    with pytest.raises(FileBatchTooLargeError) as excinfo:
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


# --------------------------------------------------------------------------- helpers


def test_check_scope_names_the_offending_label() -> None:
    with pytest.raises(InvalidFileScopeError, match="'bad label'"):
        files._check_scope(["acme", "bad label"])


def test_pair_files_with_scopes_keeps_order_and_repeats() -> None:
    paired = files._pair_files_with_scopes(["b.txt", "a.txt", "b.txt"], scope=["acme"])

    assert paired == [("b.txt", ["acme"]), ("a.txt", ["acme"]), ("b.txt", ["acme"])]


def test_pair_files_with_scopes_takes_the_scope_from_a_mapping() -> None:
    paired = files._pair_files_with_scopes({"a.txt": ["legal"]}, scope=["ignored"])

    assert paired == [("a.txt", ["legal"])]


@pytest.mark.parametrize(
    ("answer", "is_batch", "expected"),
    [
        (
            _service_error(400, "scope labels may only contain letters"),
            False,
            InvalidFileScopeError,
        ),
        (
            _service_error(400, "custom_metadata must be a JSON object"),
            False,
            InvalidFileMetadataError,
        ),
        (_service_error(413, "Batch too large"), True, FileBatchTooLargeError),
        (_service_error(422, "Value error, Uploaded file cannot be empty"), False, EmptyFileError),
        (
            _service_error(500, "Failed to store file, upload rolled back"),
            False,
            FileUploadFailedError,
        ),
        # The request line carries the database name; only the detail may match.
        (_service_error(400, "custom_metadata keys", "telescope"), False, InvalidFileMetadataError),
    ],
)
def test_translate_error_names_the_platforms_answers(answer, is_batch, expected) -> None:
    translated = files._translate_error(answer, is_batch=is_batch)

    assert isinstance(translated, expected)
    assert translated.status_code == answer.status_code
    assert str(translated) == str(answer)


@pytest.mark.parametrize(
    ("answer", "is_batch"),
    [
        (_service_error(404, "Requested endpoint does not exist."), False),
        (_service_error(413, "Request body too large"), False),  # only a batch can be too large
        (_service_error(500, "<html>upstream error</html>"), False),  # not the platform's rollback
    ],
)
def test_translate_error_leaves_unknown_answers_alone(answer, is_batch) -> None:
    assert files._translate_error(answer, is_batch=is_batch) is None
