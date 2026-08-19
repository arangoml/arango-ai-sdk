import json
import re

import httpx
import pytest
import respx

from arango_ai.exceptions import ConfigError
from arango_ai.filemanager import FILE_MANAGER_BASE, FileManagerAPI, FileUpload

from .conftest import BASE, make_jwt

RAG_BASE = f"{BASE}{FILE_MANAGER_BASE}/_db/testdb/rag-input"


@pytest.fixture(autouse=True)
def _auth() -> None:
    respx.post(f"{BASE}/_open/auth").respond(json={"jwt": make_jwt()})


@pytest.fixture
def fm(client) -> FileManagerAPI:
    return FileManagerAPI(client.http, "testdb")


def multipart_parts(request: httpx.Request) -> list[tuple[str, bytes]]:
    """(field name, body) pairs, split on the boundary from the header."""
    boundary = request.headers["content-type"].split("boundary=")[1]
    raw_parts = request.content.split(f"--{boundary}".encode())[1:-1]
    parts: list[tuple[str, bytes]] = []
    for raw in raw_parts:
        head, body = raw.split(b"\r\n\r\n", 1)
        match = re.search(rb'form-data; name="([^"]+)"', head)
        assert match is not None
        parts.append((match.group(1).decode(), body[:-2]))
    return parts


def manifest_of(request: httpx.Request) -> list[dict]:
    body = next(body for name, body in multipart_parts(request) if name == "manifest")
    return json.loads(body)


def file_bodies(request: httpx.Request) -> list[bytes]:
    return [body for name, body in multipart_parts(request) if name == "files"]


def echo_batch(request: httpx.Request) -> httpx.Response:
    """Server double: every manifest entry succeeds, echoing name + scope."""
    results = [
        {
            "name": entry["name"],
            "scope": entry["scope"],
            "status": "ok",
            "id": f"id-{entry['name']}",
            "detail": None,
        }
        for entry in manifest_of(request)
    ]
    return httpx.Response(
        200, json={"results": results, "ok_count": len(results), "error_count": 0}
    )


# -- batch upload -------------------------------------------------------------


@respx.mock
def test_upload_manifest_pairs_files_scope_and_metadata(fm) -> None:
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    result = fm.upload(
        "proj",
        [
            FileUpload("a.txt", b"alpha"),
            FileUpload(
                "b.txt",
                b"beta",
                custom_metadata={"citable_url": "https://example.com/b"},
            ),
        ],
        category="cat",
    )

    request = route.calls[0].request
    assert manifest_of(request) == [
        {"file": 0, "scope": ["proj", "cat"], "name": "a.txt"},
        {
            "file": 1,
            "scope": ["proj", "cat"],
            "name": "b.txt",
            "custom_metadata": {"citable_url": "https://example.com/b"},
        },
    ]
    assert file_bodies(request) == [b"alpha", b"beta"]
    assert [f["name"] for f in result.ok] == ["a.txt", "b.txt"]
    assert result.failed == [] and result.skipped == []


@respx.mock
def test_upload_without_category_scopes_project_only(fm) -> None:
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    fm.upload("proj", [FileUpload("a.txt", b"x")])

    assert manifest_of(route.calls[0].request)[0]["scope"] == ["proj"]


@respx.mock
def test_upload_empty_sequence_sends_nothing(fm) -> None:
    result = fm.upload("proj", [])

    assert result.ok == [] and result.failed == []


@respx.mock
def test_chunking_splits_at_file_count_cap_in_order(fm, monkeypatch) -> None:
    monkeypatch.setattr("arango_ai.filemanager.BATCH_MAX_FILES", 2)
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    files = [FileUpload(f"f{i}.txt", b"x") for i in range(5)]
    result = fm.upload("proj", files)

    assert route.call_count == 3
    manifests = [manifest_of(call.request) for call in route.calls]
    assert [[e["name"] for e in m] for m in manifests] == [
        ["f0.txt", "f1.txt"],
        ["f2.txt", "f3.txt"],
        ["f4.txt"],
    ]
    # Manifest indices point into the CHUNK's files, so they restart at 0.
    assert [e["file"] for e in manifests[1]] == [0, 1]
    assert [f["name"] for f in result.ok] == [f"f{i}.txt" for i in range(5)]


@respx.mock
def test_chunking_splits_at_byte_cap(fm, monkeypatch) -> None:
    monkeypatch.setattr("arango_ai.filemanager.BATCH_MAX_BYTES", 10)
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    fm.upload(
        "proj",
        [
            FileUpload("a.txt", b"123456"),
            FileUpload("b.txt", b"123456"),
            # Bigger than the cap: still ships, alone in its own chunk.
            FileUpload("big.txt", b"x" * 25),
        ],
    )

    manifests = [manifest_of(call.request) for call in route.calls]
    assert [[e["name"] for e in m] for m in manifests] == [
        ["a.txt"],
        ["b.txt"],
        ["big.txt"],
    ]


@respx.mock
def test_chunking_byte_cap_exact_fit_stays_one_chunk(fm, monkeypatch) -> None:
    monkeypatch.setattr("arango_ai.filemanager.BATCH_MAX_BYTES", 10)
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    # 6 + 4 bytes hit the cap exactly: the boundary is inclusive (<=), so
    # a > vs >= regression in _pack_chunks must show up here.
    fm.upload("proj", [FileUpload("a.txt", b"123456"), FileUpload("b.txt", b"1234")])

    assert route.call_count == 1
    assert [e["name"] for e in manifest_of(route.calls[0].request)] == [
        "a.txt",
        "b.txt",
    ]


@respx.mock
def test_chunk_post_uses_generous_upload_timeout(fm) -> None:
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    fm.upload("proj", [FileUpload("a.txt", b"x")])

    # Big multipart bodies + server-side batch processing outlive the
    # client-default read timeout; the chunk POST overrides it.
    timeouts = route.calls[0].request.extensions["timeout"]
    assert timeouts["read"] == 600.0


@respx.mock
def test_transport_error_fails_chunk_and_continues(fm, monkeypatch) -> None:
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

    result = fm.upload("proj", [FileUpload("a.txt", b"x"), FileUpload("b.txt", b"y")])

    assert route.call_count == 2
    assert [f["name"] for f in result.failed] == ["a.txt"]
    # A transport error leaves the chunk's server-side outcome unknown.
    assert "outcome unknown" in result.failed[0]["detail"]
    assert [f["name"] for f in result.ok] == ["b.txt"]


@respx.mock
def test_207_partial_splits_ok_and_failed(fm) -> None:
    respx.post(f"{RAG_BASE}/batch").respond(
        207,
        json={
            "results": [
                {"name": "a.txt", "scope": ["proj"], "status": "ok", "id": "1"},
                {
                    "name": "b.txt",
                    "scope": ["proj"],
                    "status": "error",
                    "id": None,
                    "detail": "empty file",
                },
            ],
            "ok_count": 1,
            "error_count": 1,
        },
    )

    result = fm.upload("proj", [FileUpload("a.txt", b"x"), FileUpload("b.txt", b"")])

    assert [f["id"] for f in result.ok] == ["1"]
    assert [(f["name"], f["detail"]) for f in result.failed] == [
        ("b.txt", "empty file")
    ]


@respx.mock
def test_whole_chunk_rejection_fails_chunk_and_continues(fm, monkeypatch) -> None:
    monkeypatch.setattr("arango_ai.filemanager.BATCH_MAX_FILES", 1)
    route = respx.post(f"{RAG_BASE}/batch")
    route.side_effect = [
        httpx.Response(400, json={"detail": "no files stored"}),
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

    result = fm.upload("proj", [FileUpload("a.txt", b"x"), FileUpload("b.txt", b"y")])

    assert route.call_count == 2
    assert [(f["name"], f["detail"]) for f in result.failed] == [
        ("a.txt", "no files stored")
    ]
    assert [f["name"] for f in result.ok] == ["b.txt"]


@respx.mock
def test_chunk_error_falls_back_to_gateway_error_shape(fm) -> None:
    respx.post(f"{RAG_BASE}/batch").respond(403, json={"error": "forbidden for role"})

    result = fm.upload("proj", [FileUpload("a.txt", b"x")])

    assert result.failed[0]["detail"] == "forbidden for role"


# -- validation and key budget --------------------------------------------------


@pytest.mark.parametrize("label", ["bad name!", "x" * 129, " cat ", ""])
@respx.mock
def test_invalid_category_labels_raise_config_error(fm, label) -> None:
    with pytest.raises(ConfigError) as excinfo:
        fm.upload("proj", [FileUpload("a.txt", b"x")], category=label)

    assert repr(label) in str(excinfo.value)


@respx.mock
def test_invalid_project_label_raises_config_error(fm) -> None:
    with pytest.raises(ConfigError):
        fm.list_files("bad project")


@respx.mock
def test_key_budget_violations_fail_before_upload(fm) -> None:
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)
    long_name = "x" * 200 + ".txt"

    result = fm.upload(
        "proj", [FileUpload(long_name, b"x"), FileUpload("ok.txt", b"x")]
    )

    assert [e["name"] for e in manifest_of(route.calls[0].request)] == ["ok.txt"]
    assert [f["name"] for f in result.failed] == [long_name]
    assert "key" in result.failed[0]["detail"]


@respx.mock
def test_key_budget_boundary_matches_studio_formula(fm) -> None:
    # db "testdb" + scope ["proj"]: key budget 216, encoded scope 15 bytes,
    # so the base64 length crosses the budget from 148 name bytes on.
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    result = fm.upload(
        "proj", [FileUpload("a" * 147, b"x"), FileUpload("a" * 148, b"x")]
    )

    assert [e["name"] for e in manifest_of(route.calls[0].request)] == ["a" * 147]
    assert [f["name"] for f in result.failed] == ["a" * 148]


# -- folder upload --------------------------------------------------------------


@respx.mock
def test_upload_folder_walks_filters_flattens_and_dedupes(
    fm, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr("arango_ai.filemanager.MAX_PARSER_FILE_BYTES", 10)
    root = tmp_path / "My Docs"
    (root / "sub").mkdir(parents=True)
    (root / ".git").mkdir()
    (root / "a.txt").write_bytes(b"a")
    (root / "sub__b.txt").write_bytes(b"clash")
    (root / "sub" / "b.txt").write_bytes(b"b")
    (root / "image.png").write_bytes(b"png")
    (root / ".hidden.txt").write_bytes(b"h")
    (root / ".git" / "c.txt").write_bytes(b"g")
    (root / "big.pdf").write_bytes(b"x" * 11)
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    result = fm.upload_folder("proj", root)

    manifest = manifest_of(route.calls[0].request)
    assert [e["name"] for e in manifest] == [
        "a.txt",
        "sub__b.txt",
        "sub__b (2).txt",
    ]
    # Default category: the folder name sanitized to a scope-safe label.
    assert manifest[0]["scope"] == ["proj", "My-Docs"]
    assert result.skipped == ["image.png"]
    assert [f["name"] for f in result.failed] == ["big.pdf"]
    assert "10 bytes" in result.failed[0]["detail"]
    assert [f["name"] for f in result.ok] == [
        "a.txt",
        "sub__b.txt",
        "sub__b (2).txt",
    ]


@respx.mock
def test_upload_folder_explicit_category_wins(fm, tmp_path) -> None:
    root = tmp_path / "irrelevant name"
    root.mkdir()
    (root / "a.md").write_bytes(b"a")
    route = respx.post(f"{RAG_BASE}/batch").mock(side_effect=echo_batch)

    fm.upload_folder("proj", str(root), category="cat")

    assert manifest_of(route.calls[0].request)[0]["scope"] == ["proj", "cat"]


@respx.mock
def test_upload_folder_requires_directory(fm, tmp_path) -> None:
    with pytest.raises(ConfigError):
        fm.upload_folder("proj", tmp_path / "nope")


# -- listing ----------------------------------------------------------------------


@respx.mock
def test_list_files_sends_repeated_scope_and_set_params(fm) -> None:
    route = respx.get(RAG_BASE).respond(
        json={"files": [], "total": 0, "limit": 100, "offset": 0}
    )

    body = fm.list_files("proj", category="cat", search="q")

    params = route.calls[0].request.url.params
    assert params.get_list("scope") == ["proj", "cat"]
    assert params["search"] == "q"
    assert params["limit"] == "100" and params["offset"] == "0"
    assert "name" not in params
    assert body == {"files": [], "total": 0, "limit": 100, "offset": 0}


@respx.mock
def test_list_files_omits_unset_filters(fm) -> None:
    route = respx.get(RAG_BASE).respond(json={"files": [], "total": 0})

    fm.list_files("proj", limit=5, offset=10)

    params = route.calls[0].request.url.params
    assert sorted(params.keys()) == ["limit", "offset", "scope"]
    assert params["limit"] == "5" and params["offset"] == "10"


@respx.mock
def test_list_categories_returns_segment_count_tuples(fm) -> None:
    route = respx.get(f"{RAG_BASE}/scopes").respond(
        json={
            "database": "testdb",
            "scope": ["proj"],
            "children": [
                {"segment": "legal", "file_count": 3},
                {"segment": "hr", "file_count": 0},
            ],
            "files": [],
        }
    )

    assert fm.list_categories("proj") == [("legal", 3), ("hr", 0)]
    assert route.calls[0].request.url.params.get_list("scope") == ["proj"]


# -- deletion ----------------------------------------------------------------------


@respx.mock
def test_delete_files_groups_all_three_outcomes(fm) -> None:
    route = respx.post(f"{RAG_BASE}/delete").respond(
        207,
        json={
            "results": [
                {"id": "f1", "status": "deleted"},
                {"id": "f2", "status": "locked"},
                {"id": "f3", "status": "not_found"},
            ]
        },
    )

    grouped = fm.delete_files(["f1", "f2", "f3"])

    assert json.loads(route.calls[0].request.content) == {"ids": ["f1", "f2", "f3"]}
    assert grouped == {"deleted": ["f1"], "locked": ["f2"], "not_found": ["f3"]}


@respx.mock
def test_delete_files_empty_sends_nothing(fm) -> None:
    assert fm.delete_files([]) == {"deleted": [], "locked": [], "not_found": []}


@respx.mock
def test_delete_category_posts_scope_body(fm) -> None:
    route = respx.post(f"{RAG_BASE}/delete-scope").respond(
        207, json={"deleted": ["f1"], "locked": ["f2"]}
    )

    result = fm.delete_category("proj", "cat")

    assert json.loads(route.calls[0].request.content) == {"scope": ["proj", "cat"]}
    assert result == {"deleted": ["f1"], "locked": ["f2"]}


# -- path handling -----------------------------------------------------------------


@respx.mock
def test_database_path_segment_is_url_encoded(client) -> None:
    fm = FileManagerAPI(client.http, "my db")
    route = respx.get(f"{BASE}{FILE_MANAGER_BASE}/_db/my%20db/rag-input").respond(
        json={"files": [], "total": 0}
    )

    fm.list_files("proj")

    assert route.called
