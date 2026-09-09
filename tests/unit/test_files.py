"""Unit tests for :class:`FileManager`: request shape, batching, validation, error mapping."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from arango_ai_sdk import files
from arango_ai_sdk.exceptions import (
    BatchTooLargeError,
    EmptyBatchError,
    EmptyFileError,
    FileUploadFailedError,
    InvalidFileMetadataError,
    InvalidScopeError,
    ServiceError,
)
from arango_ai_sdk.files import UPLOAD_TIMEOUT, FileManager

DB = "sdk_test"
RAG_INPUT = f"/_platform/filemanager/_db/{DB}/rag-input"


def stored(name: str, scope: list[str], **overrides) -> dict:
    """Return a single-upload response body as the platform shapes it."""
    body = {
        "id": f"rag-input-{name}",
        "name": name,
        "database": DB,
        "scope": scope,
        "content_type": "text/plain",
        "size": 5,
        "uploaded_at": "2026-09-08T13:29:38.165285Z",
        "version": 1,
        "safe_to_delete": True,
        "metadata_key": f"_rag_input.{DB}.{name}.v1",
        "custom_metadata": {},
    }
    body.update(overrides)
    return body


def batch_item(name: str, scope: list[str], ok: bool = True) -> dict:
    """One entry of a batch response body."""
    if not ok:
        detail = "Uploaded file cannot be empty"
        return {"name": name, "scope": scope, "status": "error", "detail": detail}
    item = stored(name, scope)
    item["status"] = "ok"
    del item["database"], item["safe_to_delete"]
    return item


def batch_body(items: list[dict]) -> dict:
    ok = sum(1 for i in items if i["status"] == "ok")
    return {"database": DB, "results": items, "ok_count": ok, "error_count": len(items) - ok}


def service_error(status: int, detail: str) -> ServiceError:
    return ServiceError(f"POST {RAG_INPUT} failed with {status}: {detail}", status_code=status)


@pytest.fixture
def manager(fake_communication, as_communication):
    """Return a FileManager over a fresh fake, together with the fake."""
    fake = fake_communication()
    return FileManager(as_communication(fake), db_name=DB), fake


@pytest.fixture
def text_file(tmp_path: Path) -> Path:
    path = tmp_path / "hello.txt"
    path.write_bytes(b"hello")
    return path


# --------------------------------------------------------------------------- upload


def test_upload_sends_one_multipart_request_with_every_field(manager, text_file: Path) -> None:
    fm, fake = manager
    fake._answers.append(stored("hello.txt", ["acme", "legal"]))

    fm.upload(text_file, scope=["acme", "legal"], custom_metadata={"author": "Ada"})

    (call,) = fake.calls
    assert (call.method, call.path) == ("post", RAG_INPUT)
    assert call.headers["content-type"].startswith("multipart/form-data; boundary=")
    assert call.timeout == UPLOAD_TIMEOUT
    assert call.part("name").text == "hello.txt"
    assert [p.text for p in call.named("scope")] == ["acme", "legal"]
    assert json.loads(call.part("custom_metadata").text) == {"author": "Ada"}
    file_part = call.part("file")
    assert (file_part.filename, file_part.content_type) == ("hello.txt", "text/plain")
    assert file_part.content == b"hello"


def test_upload_omits_optional_fields_and_honours_overrides(manager, text_file: Path) -> None:
    fm, fake = manager
    fake._answers.append(stored("renamed.bin", []))

    fm.upload(text_file, name="renamed.bin", timeout=12.5)

    (call,) = fake.calls
    assert call.timeout == 12.5
    assert {p.name for p in call.parts} == {"name", "file"}
    assert call.part("name").text == "renamed.bin"
    assert call.part("file").filename == "renamed.bin"
    # No known type for .bin: falls back to the generic binary type.
    assert call.part("file").content_type == "application/octet-stream"


def test_upload_returns_the_stored_version_parsed(manager, text_file: Path) -> None:
    fm, fake = manager
    fake._answers.append(stored("hello.txt", ["acme"], version=3, custom_metadata={"k": "v"}))

    uploaded = fm.upload(text_file, scope=["acme"])

    assert uploaded.id == "rag-input-hello.txt"
    assert uploaded.scope == ("acme",)
    assert uploaded.version == 3
    assert uploaded.metadata_key == f"_rag_input.{DB}.hello.txt.v1"
    assert uploaded.uploaded_at == datetime(2026, 9, 8, 13, 29, 38, 165285, tzinfo=UTC)
    assert uploaded.custom_metadata == {"k": "v"}
    assert uploaded.safe_to_delete is True


def test_upload_rebuilds_the_body_for_every_attempt(
    fake_communication, as_communication, text_file: Path
) -> None:
    """A retried request must not re-send an exhausted stream."""
    fake = fake_communication([stored("hello.txt", [])], attempts=2)
    fm = FileManager(as_communication(fake), db_name=DB)

    fm.upload(text_file)

    first, second = fake.calls
    assert first.part("file").content == second.part("file").content == b"hello"
    # Same boundary on both, so the single content-type header matches each body.
    assert first.headers == second.headers


def test_upload_rejects_an_empty_file_before_sending(manager, tmp_path: Path) -> None:
    fm, fake = manager
    empty = tmp_path / "empty.txt"
    empty.touch()

    with pytest.raises(EmptyFileError) as excinfo:
        fm.upload(empty)

    assert excinfo.value.status_code == 422
    assert fake.calls == []


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
def test_upload_rejects_a_bad_scope_before_sending(manager, text_file: Path, scope) -> None:
    fm, fake = manager

    with pytest.raises(InvalidScopeError) as excinfo:
        fm.upload(text_file, scope=scope)

    assert excinfo.value.status_code == 400
    assert fake.calls == []


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        (service_error(400, "scope labels may only contain letters"), InvalidScopeError),
        (service_error(400, "custom_metadata must be a JSON object"), InvalidFileMetadataError),
        (service_error(422, "Value error, Uploaded file cannot be empty"), EmptyFileError),
        (service_error(500, "Failed to store file, upload rolled back"), FileUploadFailedError),
    ],
)
def test_upload_translates_known_error_answers(manager, text_file: Path, answer, expected) -> None:
    fm, fake = manager
    fake._answers.append(answer)

    with pytest.raises(expected) as excinfo:
        fm.upload(text_file)

    assert excinfo.value.status_code == answer.status_code
    assert str(excinfo.value) == str(answer)
    assert excinfo.value.__cause__ is answer


@pytest.mark.parametrize(
    "answer",
    [
        service_error(404, "Requested endpoint does not exist."),
        service_error(413, "Request body too large"),  # only a batch can be too large
        service_error(500, "<html>upstream error</html>"),  # not the platform's own rollback
    ],
)
def test_upload_reraises_unknown_error_answers_unchanged(manager, text_file: Path, answer) -> None:
    fm, fake = manager
    fake._answers.append(answer)

    with pytest.raises(ServiceError) as excinfo:
        fm.upload(text_file)

    assert excinfo.value is answer


def test_error_classification_ignores_the_database_name(
    fake_communication, as_communication, text_file
):
    """The request line carries the database name; only the platform's detail counts."""
    fake = fake_communication()
    fm = FileManager(as_communication(fake), db_name="telescope")
    path = "/_platform/filemanager/_db/telescope/rag-input"
    fake._answers.append(
        ServiceError(
            f"POST {path} failed with 400: custom_metadata keys must be strings", status_code=400
        )
    )

    with pytest.raises(InvalidFileMetadataError):
        fm.upload(text_file)


def test_upload_refuses_a_folder_or_a_missing_path_before_sending(manager, tmp_path: Path) -> None:
    fm, fake = manager

    with pytest.raises(IsADirectoryError):
        fm.upload(tmp_path)
    with pytest.raises(FileNotFoundError):
        fm.upload(tmp_path / "missing.txt")

    assert fake.calls == []


# --------------------------------------------------------------------------- upload_many


def test_upload_many_sends_a_manifest_and_the_files_in_order(manager, tmp_path: Path) -> None:
    fm, fake = manager
    a, b = tmp_path / "a.txt", tmp_path / "b.pdf"
    a.write_bytes(b"aaa")
    b.write_bytes(b"bbbb")
    fake._answers.append(batch_body([batch_item("a.txt", ["acme"]), batch_item("b.pdf", ["acme"])]))

    result = fm.upload_many([a, b], scope=["acme"], custom_metadata={"source": "test"})

    (call,) = fake.calls
    assert call.path == f"{RAG_INPUT}/batch"
    assert json.loads(call.part("manifest").text) == [
        {"file": 0, "name": "a.txt", "scope": ["acme"]},
        {"file": 1, "name": "b.pdf", "scope": ["acme"]},
    ]
    assert json.loads(call.part("custom_metadata").text) == {"source": "test"}
    assert [(p.filename, p.content_type, p.content) for p in call.named("files")] == [
        ("a.txt", "text/plain", b"aaa"),
        ("b.pdf", "application/pdf", b"bbbb"),
    ]
    assert (result.ok_count, result.error_count) == (2, 0)
    assert [r.name for r in result.results] == ["a.txt", "b.pdf"]
    assert result.results[0].ok and result.results[0].scope == ("acme",)


def test_upload_many_returns_partial_failures_as_results(manager, tmp_path: Path) -> None:
    fm, fake = manager
    good, bad = tmp_path / "good.txt", tmp_path / "bad.txt"
    good.write_bytes(b"x")
    bad.write_bytes(b"y")
    items = [batch_item("good.txt", []), batch_item("bad.txt", [], ok=False)]
    fake._answers.append(batch_body(items))

    result = fm.upload_many([good, bad])

    assert (result.ok_count, result.error_count) == (1, 1)
    (failed,) = result.failed
    assert (failed.name, failed.ok) == ("bad.txt", False)
    assert failed.detail == "Uploaded file cannot be empty"
    assert failed.id is None and failed.uploaded_at is None


def test_upload_many_splits_into_requests_of_at_most_a_hundred(manager, tmp_path: Path) -> None:
    fm, fake = manager
    paths = []
    for i in range(250):
        path = tmp_path / f"f{i:03d}.txt"
        path.write_bytes(b"x")
        paths.append(path)
    for size in (100, 100, 50):
        fake._answers.append(batch_body([batch_item(f"f{i}.txt", []) for i in range(size)]))

    result = fm.upload_many(paths)

    assert [len(c.named("files")) for c in fake.calls] == [100, 100, 50]
    # Manifest indexes restart per request, since they address that request's parts.
    third = json.loads(fake.calls[2].part("manifest").text)
    assert [e["file"] for e in third] == list(range(50))
    assert third[0]["name"] == "f200.txt"
    assert (len(result.results), result.ok_count) == (250, 250)


def test_upload_many_rejects_an_empty_list_before_sending(manager) -> None:
    fm, fake = manager

    with pytest.raises(EmptyBatchError):
        fm.upload_many([])

    assert fake.calls == []


def test_upload_many_refuses_an_oversized_file_before_sending_anything(
    manager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The size check runs over the whole set first, even for a file in a later request."""
    fm, fake = manager
    monkeypatch.setattr(files, "BATCH_MAX_BYTES", 10)
    small = [tmp_path / f"s{i}.txt" for i in range(3)]
    for path in small:
        path.write_bytes(b"x")
    huge = tmp_path / "huge.bin"
    huge.write_bytes(b"x" * 11)

    with pytest.raises(BatchTooLargeError):
        fm.upload_many([*small, huge])

    assert fake.calls == []


def test_upload_many_reports_a_failed_request_through_its_files(manager, tmp_path: Path) -> None:
    """One request failing as a whole must not hide the others or stop them."""
    fm, fake = manager
    paths = []
    for i in range(250):
        path = tmp_path / f"f{i:03d}.txt"
        path.write_bytes(b"x")
        paths.append(path)
    fake._answers.append(batch_body([batch_item(f"f{i:03d}.txt", []) for i in range(100)]))
    fake._answers.append(
        service_error(500, "Batch upload failed: every file hit an internal error")
    )
    fake._answers.append(batch_body([batch_item(f"f{i:03d}.txt", []) for i in range(200, 250)]))

    result = fm.upload_many(paths)

    assert len(fake.calls) == 3
    assert (result.ok_count, result.error_count) == (150, 100)
    assert [r.name for r in result.failed] == [f"f{i:03d}.txt" for i in range(100, 200)]
    assert "internal error" in (result.failed[0].detail or "")
    assert result.results[199].scope == ()


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        (service_error(400, "custom_metadata must be a JSON object"), InvalidFileMetadataError),
        (service_error(413, "Batch too large"), BatchTooLargeError),
    ],
)
def test_upload_many_raises_errors_the_caller_has_to_fix(manager, tmp_path: Path, answer, expected):
    fm, fake = manager
    path = tmp_path / "a.txt"
    path.write_bytes(b"a")
    fake._answers.append(answer)

    with pytest.raises(expected):
        fm.upload_many([path])


# --------------------------------------------------------------------------- batching by size


def planned(name: str, size: int) -> files._Planned:
    return files._Planned(Path(name), name, (), size)


def test_batches_split_by_total_bytes_and_keep_order() -> None:
    gib = 1024**3
    plan = [planned("a", gib), planned("b", gib), planned("c", 1), planned("d", 2 * gib)]

    batches = list(files._batches(plan))

    assert [[p.name for p in b] for b in batches] == [["a", "b"], ["c"], ["d"]]


def test_batches_refuse_a_single_file_over_the_request_limit() -> None:
    with pytest.raises(BatchTooLargeError) as excinfo:
        list(files._batches([planned("huge", files.BATCH_MAX_BYTES + 1)]))

    assert excinfo.value.status_code == 413
    assert "huge" in str(excinfo.value)


# --------------------------------------------------------------------------- upload_folder


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    (tmp_path / "root.txt").write_bytes(b"r")
    (tmp_path / "legal").mkdir()
    (tmp_path / "legal" / "nda.pdf").write_bytes(b"n")
    (tmp_path / "legal" / "2026").mkdir()
    (tmp_path / "legal" / "2026" / "q1.pdf").write_bytes(b"q")
    return tmp_path


def test_upload_folder_flattens_by_default(manager, tree: Path) -> None:
    fm, fake = manager
    names = ("q1.pdf", "nda.pdf", "root.txt")
    fake._answers.append(batch_body([batch_item(n, ["acme"]) for n in names]))

    fm.upload_folder(tree, scope=["acme"])

    manifest = json.loads(fake.calls[0].part("manifest").text)
    assert [(e["name"], e["scope"]) for e in manifest] == [
        ("q1.pdf", ["acme"]),
        ("nda.pdf", ["acme"]),
        ("root.txt", ["acme"]),
    ]


def test_upload_folder_can_turn_subfolders_into_scope_labels(manager, tree: Path) -> None:
    fm, fake = manager
    fake._answers.append(batch_body([batch_item("x", []) for _ in range(3)]))

    fm.upload_folder(tree, scope=["acme"], preserve_paths=True)

    manifest = json.loads(fake.calls[0].part("manifest").text)
    assert [(e["name"], e["scope"]) for e in manifest] == [
        ("q1.pdf", ["acme", "legal", "2026"]),
        ("nda.pdf", ["acme", "legal"]),
        ("root.txt", ["acme"]),
    ]


def test_upload_folder_rejects_a_subfolder_name_the_platform_refuses(
    manager, tmp_path: Path
) -> None:
    fm, fake = manager
    (tmp_path / "bad name").mkdir()
    (tmp_path / "bad name" / "f.txt").write_bytes(b"f")

    with pytest.raises(InvalidScopeError):
        fm.upload_folder(tmp_path, preserve_paths=True)

    assert fake.calls == []


def test_upload_folder_rejects_an_empty_folder_before_sending(manager, tmp_path: Path) -> None:
    fm, fake = manager

    with pytest.raises(EmptyBatchError):
        fm.upload_folder(tmp_path)

    assert fake.calls == []


def test_upload_folder_refuses_a_missing_path_or_a_file(manager, text_file: Path) -> None:
    fm, fake = manager

    with pytest.raises(NotADirectoryError):
        fm.upload_folder(text_file.parent / "missing")
    with pytest.raises(NotADirectoryError):
        fm.upload_folder(text_file)

    assert fake.calls == []
