import json

import pytest
from typer.testing import CliRunner

from aweave.docs.cli import app

pytestmark = pytest.mark.usefixtures("temp_db")


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def temp_db(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = tmp_path / "test_docstore.db"
    monkeypatch.setenv("AWEAVE_DB_PATH", str(db_path))
    return db_path


def _parse_json(output: str) -> dict:
    return json.loads(output)


def test_create_with_content(runner: CliRunner):
    result = runner.invoke(app, ["create", "--summary", "Test doc", "--content", "Hello world"])
    assert result.exit_code == 0
    data = _parse_json(result.output)
    assert data["success"] is True
    payload = data["content"][0]["data"]
    assert payload["version"] == 1
    assert "document_id" in payload


def test_create_with_file(runner: CliRunner, tmp_path):
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test content", encoding="utf-8")
    result = runner.invoke(app, ["create", "--summary", "From file", "--file", str(test_file)])
    assert result.exit_code == 0
    data = _parse_json(result.output)
    assert data["success"] is True


def test_create_requires_one_source(runner: CliRunner):
    result = runner.invoke(app, ["create", "--summary", "No content"])
    assert result.exit_code == 4
    data = _parse_json(result.output)
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_INPUT"


def test_create_rejects_plain_format(runner: CliRunner):
    result = runner.invoke(
        app, ["create", "--summary", "Test", "--content", "x", "--format", "plain"]
    )
    assert result.exit_code == 4
    data = _parse_json(result.output)
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_INPUT"


def test_submit_new_version(runner: CliRunner):
    result = runner.invoke(app, ["create", "--summary", "v1", "--content", "Version 1"])
    doc_id = _parse_json(result.output)["content"][0]["data"]["document_id"]
    result = runner.invoke(app, ["submit", doc_id, "--summary", "v2", "--content", "Version 2"])
    assert result.exit_code == 0
    data = _parse_json(result.output)
    assert data["success"] is True
    assert data["content"][0]["data"]["version"] == 2


def test_submit_nonexistent_doc(runner: CliRunner):
    result = runner.invoke(app, ["submit", "nope", "--summary", "v2", "--content", "test"])
    assert result.exit_code == 2
    data = _parse_json(result.output)
    assert data["error"]["code"] == "DOC_NOT_FOUND"


def test_get_latest_json(runner: CliRunner):
    result = runner.invoke(app, ["create", "--summary", "Test", "--content", "Content here"])
    doc_id = _parse_json(result.output)["content"][0]["data"]["document_id"]
    result = runner.invoke(app, ["get", doc_id])
    assert result.exit_code == 0
    data = _parse_json(result.output)
    assert data["content"][0]["data"]["content"] == "Content here"


def test_get_plain_format(runner: CliRunner):
    result = runner.invoke(app, ["create", "--summary", "Test", "--content", "Raw content"])
    doc_id = _parse_json(result.output)["content"][0]["data"]["document_id"]
    result = runner.invoke(app, ["get", doc_id, "--format", "plain"])
    assert result.exit_code == 0
    assert result.output.strip() == "Raw content"


def test_list_and_delete_semantics(runner: CliRunner):
    runner.invoke(app, ["create", "--summary", "Doc 1", "--content", "c1"])
    result2 = runner.invoke(app, ["create", "--summary", "Doc 2", "--content", "c2"])
    doc_id_2 = _parse_json(result2.output)["content"][0]["data"]["document_id"]

    result = runner.invoke(app, ["list"])
    data = _parse_json(result.output)
    assert result.exit_code == 0
    assert data["total_count"] == 2

    result = runner.invoke(app, ["delete", doc_id_2])
    assert result.exit_code == 4

    result = runner.invoke(app, ["delete", doc_id_2, "--confirm"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["list"])
    data = _parse_json(result.output)
    assert data["total_count"] == 1

    result = runner.invoke(app, ["list", "--include-deleted"])
    data = _parse_json(result.output)
    assert data["total_count"] == 2


def test_metadata_must_be_object(runner: CliRunner):
    result = runner.invoke(app, ["create", "--summary", "m", "--content", "x", "--metadata", "[]"])
    assert result.exit_code == 4
    data = _parse_json(result.output)
    assert data["error"]["code"] == "INVALID_INPUT"
