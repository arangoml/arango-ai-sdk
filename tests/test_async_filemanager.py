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
