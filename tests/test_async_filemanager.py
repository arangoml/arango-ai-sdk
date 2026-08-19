import httpx
import pytest
import respx

from arango_ai.filemanager import FILE_MANAGER_BASE, FileUpload

from .conftest import BASE, make_jwt
from .test_filemanager import echo_batch, file_bodies, manifest_of

RAG_BASE = f"{BASE}{FILE_MANAGER_BASE}/_db/testdb/rag-input"


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


@respx.mock
async def test_upload_manifest_pairs_files_scope_and_metadata(async_client) -> None:
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    result = await async_client.files.upload(
        "proj",
        [
            FileUpload("a.txt", b"alpha"),
            FileUpload(
                "b.txt",
                b"beta",
                custom_metadata={"citable_url": "https://example.com/b"},
            ),
        ],
        category="docs",
    )

    assert [entry["name"] for entry in result.ok] == ["a.txt", "b.txt"]
    assert result.failed == []
    request = route.calls[0].request
    manifest = manifest_of(request)
    assert manifest[0] == {"file": 0, "scope": ["proj", "docs"], "name": "a.txt"}
    assert manifest[1]["custom_metadata"] == {"citable_url": "https://example.com/b"}
    assert file_bodies(request) == [b"alpha", b"beta"]


@respx.mock
async def test_rejected_chunk_fails_per_file_with_server_detail(async_client) -> None:
    respx.post(f"{RAG_BASE}/batch").mock(
        return_value=httpx.Response(413, json={"detail": "too large"})
    )

    result = await async_client.files.upload("proj", [FileUpload("a.txt", b"x")])

    assert result.ok == []
    assert [entry["detail"] for entry in result.failed] == ["too large"]


@respx.mock
async def test_key_budget_violations_fail_before_upload(async_client) -> None:
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)
    long_name = "x" * 200 + ".txt"

    result = await async_client.files.upload(
        "proj", [FileUpload(long_name, b"x"), FileUpload("ok.txt", b"x")]
    )

    # The doomed file lands in failed and never travels in the manifest.
    assert [e["name"] for e in manifest_of(route.calls[0].request)] == ["ok.txt"]
    assert [f["name"] for f in result.failed] == [long_name]
    assert "key" in result.failed[0]["detail"]


@respx.mock
async def test_upload_folder_propagates_skipped_and_oversized(
    async_client, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("arango_ai.filemanager.MAX_PARSER_FILE_BYTES", 10)
    root = tmp_path / "docs"
    root.mkdir()
    (root / "a.txt").write_bytes(b"a")
    (root / "image.png").write_bytes(b"png")
    (root / "big.pdf").write_bytes(b"x" * 11)
    respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    result = await async_client.files.upload_folder("proj", root)

    assert [f["name"] for f in result.ok] == ["a.txt"]
    assert result.skipped == ["image.png"]
    assert [f["name"] for f in result.failed] == ["big.pdf"]
    assert "10 bytes" in result.failed[0]["detail"]


@respx.mock
async def test_transport_error_fails_chunk_and_continues(
    async_client, monkeypatch
) -> None:
    monkeypatch.setattr("arango_ai.filemanager.BATCH_MAX_FILES", 1)
    route = respx.post(f"{RAG_BASE}/batch")
    route.side_effect = [
        httpx.ConnectError("boom"),
        httpx.Response(
            200,
            json={
                "results": [
                    {"name": "b.txt", "scope": ["proj"], "status": "ok", "id": "2"}
                ],
                "ok_count": 1,
                "error_count": 0,
            },
        ),
    ]

    result = await async_client.files.upload(
        "proj", [FileUpload("a.txt", b"x"), FileUpload("b.txt", b"y")]
    )

    assert route.call_count == 2
    assert [f["name"] for f in result.failed] == ["a.txt"]
    # A transport error leaves the chunk's server-side outcome unknown.
    assert "outcome unknown" in result.failed[0]["detail"]
    assert [f["name"] for f in result.ok] == ["b.txt"]
