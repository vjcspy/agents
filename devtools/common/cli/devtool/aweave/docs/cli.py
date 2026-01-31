"""Document store CLI commands."""

from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, Any

import typer

from aweave.mcp.response import ContentType, MCPContent, MCPError, MCPResponse

from . import db

app = typer.Typer(help="Document storage for AI agents")


class OutputFormat(str, Enum):
    json = "json"
    markdown = "markdown"
    plain = "plain"


def _output(response: MCPResponse, fmt: OutputFormat) -> None:
    if fmt == OutputFormat.json:
        typer.echo(response.to_json())
    else:
        typer.echo(response.to_markdown())


def _output_error_for_plain_request(response: MCPResponse, fmt: OutputFormat) -> None:
    if fmt == OutputFormat.plain:
        _output(response, OutputFormat.json)
    else:
        _output(response, fmt)


def _error_response(code: str, message: str, suggestion: str | None = None) -> MCPResponse:
    return MCPResponse(success=False, error=MCPError(code=code, message=message, suggestion=suggestion))


def _reject_plain_format(command: str, fmt: OutputFormat) -> bool:
    if fmt != OutputFormat.plain:
        return False

    _output(
        _error_response(
            "INVALID_INPUT",
            f"--format plain is not supported for '{command}' command",
            "Use --format json or --format markdown",
        ),
        OutputFormat.json,
    )
    raise typer.Exit(code=4)


def _parse_metadata(metadata_str: str, fmt: OutputFormat) -> dict[str, Any]:
    try:
        parsed = json.loads(metadata_str)
    except json.JSONDecodeError as e:
        _output(
            _error_response(
                "INVALID_INPUT",
                f"Invalid JSON in --metadata: {e}",
                "Provide valid JSON object, e.g. '{\"key\": \"value\"}'",
            ),
            fmt,
        )
        raise typer.Exit(code=4) from None

    if not isinstance(parsed, dict):
        _output(
            _error_response(
                "INVALID_INPUT",
                f"--metadata must be a JSON object, got {type(parsed).__name__}",
                "Provide JSON object, not array/string/number/null",
            ),
            fmt,
        )
        raise typer.Exit(code=4) from None

    return parsed


def _read_content(
    file: Path | None,
    content: str | None,
    stdin: bool,
    fmt: OutputFormat,
) -> str:
    sources = int(file is not None) + int(content is not None) + int(stdin)
    if sources == 0:
        _output(
            _error_response(
                "INVALID_INPUT",
                "No content provided",
                "Use --file, --content, or --stdin to provide content",
            ),
            fmt,
        )
        raise typer.Exit(code=4)

    if sources > 1:
        _output(
            _error_response(
                "INVALID_INPUT",
                "Multiple content sources provided",
                "Use only one of --file, --content, or --stdin",
            ),
            fmt,
        )
        raise typer.Exit(code=4)

    if stdin:
        return sys.stdin.read()

    if file is not None:
        if not file.exists():
            _output(
                _error_response(
                    "FILE_NOT_FOUND",
                    f"File not found: {file}",
                    "Check the file path and try again",
                ),
                fmt,
            )
            raise typer.Exit(code=1)
        return file.read_text(encoding="utf-8")

    return content or ""


@app.command()
def create(
    summary: Annotated[str, typer.Option("--summary", "-s", help="Document summary")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Path to content file")] = None,
    content: Annotated[str | None, typer.Option("--content", help="Inline content")] = None,
    stdin: Annotated[bool, typer.Option("--stdin", help="Read content from stdin")] = False,
    metadata: Annotated[str, typer.Option("--metadata", help="JSON metadata object")] = "{}",
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    _reject_plain_format("create", fmt)
    meta = _parse_metadata(metadata, fmt)
    doc_content = _read_content(file, content, stdin, fmt)

    try:
        result = db.create_document(summary=summary, content=doc_content, metadata=meta)
    except Exception as e:
        _output(_error_response("DB_ERROR", str(e)), fmt)
        raise typer.Exit(code=3) from None

    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=result)],
        metadata={"message": "Document created successfully"},
    )
    _output(response, fmt)


@app.command()
def submit(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    summary: Annotated[str, typer.Option("--summary", "-s", help="Version summary")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Path to content file")] = None,
    content: Annotated[str | None, typer.Option("--content", help="Inline content")] = None,
    stdin: Annotated[bool, typer.Option("--stdin", help="Read content from stdin")] = False,
    metadata: Annotated[str, typer.Option("--metadata", help="JSON metadata object")] = "{}",
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    _reject_plain_format("submit", fmt)
    meta = _parse_metadata(metadata, fmt)
    doc_content = _read_content(file, content, stdin, fmt)

    try:
        result = db.submit_version(document_id=document_id, summary=summary, content=doc_content, metadata=meta)
    except Exception as e:
        _output(_error_response("DB_ERROR", str(e)), fmt)
        raise typer.Exit(code=3) from None

    if result is None:
        _output(
            _error_response(
                "DOC_NOT_FOUND",
                f"Document '{document_id}' not found or deleted",
                "Use 'aw docs list' to see available documents",
            ),
            fmt,
        )
        raise typer.Exit(code=2)

    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=result)],
        metadata={"message": f"Version {result['version']} submitted successfully"},
    )
    _output(response, fmt)


@app.command()
def get(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    version: Annotated[int | None, typer.Option("--version", "-v", help="Specific version")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.plain,
) -> None:
    if fmt == OutputFormat.plain:
        pass
    elif fmt not in (OutputFormat.json, OutputFormat.markdown):
        _output(_error_response("INVALID_INPUT", f"Unknown format: {fmt}"), OutputFormat.json)
        raise typer.Exit(code=4)

    try:
        doc = db.get_document(document_id=document_id, version=version)
    except Exception as e:
        _output_error_for_plain_request(_error_response("DB_ERROR", str(e)), fmt)
        raise typer.Exit(code=3) from None

    if doc is None:
        code = "DOC_NOT_FOUND" if version is None else "VERSION_NOT_FOUND"
        msg = f"Document '{document_id}' not found" if version is None else f"Document '{document_id}' version {version} not found"
        _output_error_for_plain_request(
            _error_response(code, msg, "Use 'aw docs list' or 'aw docs history' to inspect available documents"),
            fmt,
        )
        raise typer.Exit(code=2)

    if fmt == OutputFormat.plain:
        typer.echo(doc["content"])
        return

    response = MCPResponse(success=True, content=[MCPContent(type=ContentType.JSON, data=doc)])
    _output(response, fmt)


@app.command("list")
def list_docs(
    limit: Annotated[int | None, typer.Option("--limit", "-l", help="Max documents")] = None,
    include_deleted: Annotated[bool, typer.Option("--include-deleted", help="Include soft-deleted")] = False,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    _reject_plain_format("list", fmt)

    try:
        documents, total = db.list_documents(limit=limit, include_deleted=include_deleted)
    except Exception as e:
        _output(_error_response("DB_ERROR", str(e)), fmt)
        raise typer.Exit(code=3) from None

    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data={"documents": documents})],
        total_count=total,
        has_more=limit is not None and len(documents) < total,
    )
    _output(response, fmt)


@app.command()
def history(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    limit: Annotated[int | None, typer.Option("--limit", "-l", help="Max versions")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    _reject_plain_format("history", fmt)

    try:
        versions, total = db.get_history(document_id=document_id, limit=limit)
    except Exception as e:
        _output(_error_response("DB_ERROR", str(e)), fmt)
        raise typer.Exit(code=3) from None

    if total == 0:
        _output(
            _error_response(
                "DOC_NOT_FOUND",
                f"Document '{document_id}' not found or deleted",
                "Use 'aw docs list' to see available documents",
            ),
            fmt,
        )
        raise typer.Exit(code=2)

    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data={"document_id": document_id, "versions": versions})],
        total_count=total,
        has_more=limit is not None and len(versions) < total,
    )
    _output(response, fmt)


@app.command()
def export(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file path")],
    version: Annotated[int | None, typer.Option("--version", "-v", help="Specific version")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    _reject_plain_format("export", fmt)

    try:
        doc = db.get_document(document_id=document_id, version=version)
    except Exception as e:
        _output(_error_response("DB_ERROR", str(e)), fmt)
        raise typer.Exit(code=3) from None

    if doc is None:
        _output(
            _error_response(
                "DOC_NOT_FOUND" if version is None else "VERSION_NOT_FOUND",
                f"Document '{document_id}' not found" if version is None else f"Document '{document_id}' version {version} not found",
                "Use 'aw docs list' or 'aw docs history' to inspect available documents",
            ),
            fmt,
        )
        raise typer.Exit(code=2)

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(doc["content"], encoding="utf-8")
    except Exception as e:
        _output(_error_response("INVALID_INPUT", str(e)), fmt)
        raise typer.Exit(code=1) from None

    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.TEXT, text=f"Exported to {output}")],
        metadata={"path": str(output), "version": doc["version"]},
    )
    _output(response, fmt)


@app.command()
def delete(
    document_id: Annotated[str, typer.Argument(help="Document ID")],
    confirm: Annotated[bool, typer.Option("--confirm", help="Confirm deletion")] = False,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    _reject_plain_format("delete", fmt)

    if not confirm:
        _output(
            _error_response(
                "INVALID_INPUT",
                "Deletion requires confirmation",
                "Add --confirm flag to proceed",
            ),
            fmt,
        )
        raise typer.Exit(code=4)

    try:
        affected = db.soft_delete_document(document_id=document_id)
    except Exception as e:
        _output(_error_response("DB_ERROR", str(e)), fmt)
        raise typer.Exit(code=3) from None

    if affected == 0:
        _output(
            _error_response(
                "DOC_NOT_FOUND",
                f"Document '{document_id}' not found or already deleted",
                "Use 'aw docs list' to see available documents",
            ),
            fmt,
        )
        raise typer.Exit(code=2)

    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.TEXT, text="Document soft-deleted")],
        metadata={"document_id": document_id, "versions_affected": affected},
    )
    _output(response, fmt)


if __name__ == "__main__":
    app()
