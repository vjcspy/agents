"""Debate CLI commands."""

from __future__ import annotations

import sys
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Annotated, Any

import httpx
import typer

from aweave.http.client import HTTPClient, HTTPClientError
from aweave.mcp.response import ContentType, MCPContent, MCPError, MCPResponse

from .config import DEBATE_AUTH_TOKEN, DEBATE_SERVER_URL, DEBATE_WAIT_DEADLINE, POLL_TIMEOUT

app = typer.Typer(help="Debate CLI - AI Agent debate management")


class OutputFormat(str, Enum):
    json = "json"
    markdown = "markdown"


def _get_client(timeout: int = 30) -> HTTPClient:
    """Get HTTP client with auth if configured."""
    headers = {}
    if DEBATE_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {DEBATE_AUTH_TOKEN}"
    return HTTPClient(base_url=DEBATE_SERVER_URL, headers=headers, timeout=timeout)


def _get_poll_client() -> HTTPClient:
    """Get HTTP client for long polling with extended timeout."""
    headers = {}
    if DEBATE_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {DEBATE_AUTH_TOKEN}"
    return HTTPClient(base_url=DEBATE_SERVER_URL, headers=headers, timeout=POLL_TIMEOUT)


def _output(response: MCPResponse, fmt: OutputFormat) -> None:
    """Output response in requested format."""
    if fmt == OutputFormat.json:
        typer.echo(response.to_json())
    else:
        typer.echo(response.to_markdown())


def _error_response(code: str, message: str, suggestion: str | None = None) -> MCPResponse:
    """Create error response."""
    return MCPResponse(success=False, error=MCPError(code=code, message=message, suggestion=suggestion))


def _handle_server_error(e: HTTPClientError, fmt: OutputFormat) -> None:
    """Handle server error and exit."""
    exit_code = {
        "NOT_FOUND": 2,
        "DEBATE_NOT_FOUND": 2,
        "ARGUMENT_NOT_FOUND": 2,
        "INVALID_INPUT": 4,
        "ACTION_NOT_ALLOWED": 5,
        "AUTH_FAILED": 6,
        "FORBIDDEN": 6,
    }.get(e.code, 3)

    _output(
        MCPResponse(
            success=False,
            error=MCPError(code=e.code, message=e.message, suggestion=e.suggestion),
        ),
        fmt,
    )
    raise typer.Exit(code=exit_code)


def _read_content(
    file: Path | None,
    content: str | None,
    stdin: bool,
    fmt: OutputFormat,
) -> str | None:
    """Read content from file, inline, or stdin. Returns None if invalid."""
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
        return None

    if sources > 1:
        _output(
            _error_response(
                "INVALID_INPUT",
                "Multiple content sources provided",
                "Use only one of --file, --content, or --stdin",
            ),
            fmt,
        )
        return None

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
            return None
        return file.read_text(encoding="utf-8")

    return content or ""


@app.command("generate-id")
def generate_id(
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """Generate a new debate UUID."""
    new_id = str(uuid.uuid4())
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data={"debate_id": new_id})],
        metadata={"message": "Use this ID with 'aw debate create'"},
    )
    _output(response, fmt)


@app.command()
def create(
    debate_id: Annotated[str, typer.Option("--debate-id", help="Debate UUID")],
    title: Annotated[str, typer.Option("--title", help="Debate title")],
    debate_type: Annotated[str, typer.Option("--type", help="Debate type: coding_plan_debate|general_debate")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Path to motion content file")] = None,
    content: Annotated[str | None, typer.Option("--content", help="Inline motion content")] = None,
    stdin: Annotated[bool, typer.Option("--stdin", help="Read motion content from stdin")] = False,
    client_request_id: Annotated[str | None, typer.Option("--client-request-id", help="Idempotency key")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """Create a new debate with MOTION."""
    motion_content = _read_content(file, content, stdin, fmt)
    if motion_content is None:
        raise typer.Exit(code=4)

    req_id = client_request_id or str(uuid.uuid4())

    try:
        client = _get_client()
        resp = client.post(
            "/debates",
            json={
                "debate_id": debate_id,
                "title": title,
                "debate_type": debate_type,
                "motion_content": motion_content,
                "client_request_id": req_id,
            },
        )
    except HTTPClientError as e:
        _handle_server_error(e, fmt)

    data = resp.get("data", {})
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=data)],
        metadata={"message": "Debate created successfully", "client_request_id": req_id},
    )
    _output(response, fmt)


@app.command("get-context")
def get_context(
    debate_id: Annotated[str, typer.Option("--debate-id", help="Debate UUID")],
    limit: Annotated[int | None, typer.Option("--limit", "-l", help="Number of recent arguments")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """Get debate context (debate + motion + arguments)."""
    try:
        client = _get_client()
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = str(limit)
        resp = client.get(f"/debates/{debate_id}", params=params or None)
    except HTTPClientError as e:
        _handle_server_error(e, fmt)

    data = resp.get("data", {})
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=data)],
    )
    _output(response, fmt)


@app.command()
def submit(
    debate_id: Annotated[str, typer.Option("--debate-id", help="Debate UUID")],
    role: Annotated[str, typer.Option("--role", help="Role: proposer|opponent")],
    target_id: Annotated[str, typer.Option("--target-id", help="Target argument UUID")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Path to content file")] = None,
    content: Annotated[str | None, typer.Option("--content", help="Inline content")] = None,
    stdin: Annotated[bool, typer.Option("--stdin", help="Read content from stdin")] = False,
    client_request_id: Annotated[str | None, typer.Option("--client-request-id", help="Idempotency key")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """Submit a CLAIM argument."""
    arg_content = _read_content(file, content, stdin, fmt)
    if arg_content is None:
        raise typer.Exit(code=4)

    req_id = client_request_id or str(uuid.uuid4())

    try:
        client = _get_client()
        resp = client.post(
            f"/debates/{debate_id}/arguments",
            json={
                "role": role,
                "target_id": target_id,
                "content": arg_content,
                "client_request_id": req_id,
            },
        )
    except HTTPClientError as e:
        _handle_server_error(e, fmt)

    data = resp.get("data", {})
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=data)],
        metadata={"message": "Argument submitted", "client_request_id": req_id},
    )
    _output(response, fmt)


@app.command()
def wait(
    debate_id: Annotated[str, typer.Option("--debate-id", help="Debate UUID")],
    role: Annotated[str, typer.Option("--role", help="Role: proposer|opponent")],
    argument_id: Annotated[str | None, typer.Option("--argument-id", help="Last seen argument UUID")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """Wait for a new argument (long polling)."""
    client = _get_poll_client()
    start = time.time()
    deadline = DEBATE_WAIT_DEADLINE
    last_seen_seq = 0

    while time.time() - start < deadline:
        try:
            resp = client.get(
                f"/debates/{debate_id}/wait",
                params={"argument_id": argument_id or "", "role": role},
            )
            # Server returns {success, data}
            data = resp.get("data", {})

            if data.get("has_new_argument"):
                response = MCPResponse(
                    success=True,
                    content=[
                        MCPContent(
                            type=ContentType.JSON,
                            data={
                                "status": "new_argument",
                                "action": data["action"],
                                "debate_state": data["debate_state"],
                                "argument": data["argument"],
                                "next_argument_id_to_wait": data["argument"]["id"],
                            },
                        )
                    ],
                )
                _output(response, fmt)
                return

            # has_new_argument=False → server poll timeout, retry
            last_seen_seq = data.get("last_seen_seq", last_seen_seq)

        except httpx.TimeoutException:
            # Connection/read timeout - retry
            continue
        except HTTPClientError as e:
            _handle_server_error(e, fmt)

    # Overall deadline reached - timeout is expected, not error
    response = MCPResponse(
        success=True,
        content=[
            MCPContent(
                type=ContentType.JSON,
                data={
                    "status": "timeout",
                    "message": f"No response after {deadline}s",
                    "debate_id": debate_id,
                    "last_argument_id": argument_id,
                    "last_seen_seq": last_seen_seq,
                },
            )
        ],
    )
    _output(response, fmt)


@app.command()
def appeal(
    debate_id: Annotated[str, typer.Option("--debate-id", help="Debate UUID")],
    target_id: Annotated[str, typer.Option("--target-id", help="Target argument UUID")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Path to content file")] = None,
    content: Annotated[str | None, typer.Option("--content", help="Inline content")] = None,
    stdin: Annotated[bool, typer.Option("--stdin", help="Read content from stdin")] = False,
    client_request_id: Annotated[str | None, typer.Option("--client-request-id", help="Idempotency key")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """Submit an APPEAL to request Arbitrator ruling."""
    arg_content = _read_content(file, content, stdin, fmt)
    if arg_content is None:
        raise typer.Exit(code=4)

    req_id = client_request_id or str(uuid.uuid4())

    try:
        client = _get_client()
        resp = client.post(
            f"/debates/{debate_id}/appeal",
            json={
                "target_id": target_id,
                "content": arg_content,
                "client_request_id": req_id,
            },
        )
    except HTTPClientError as e:
        _handle_server_error(e, fmt)

    data = resp.get("data", {})
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=data)],
        metadata={"message": "Appeal submitted", "client_request_id": req_id},
    )
    _output(response, fmt)


@app.command("request-completion")
def request_completion(
    debate_id: Annotated[str, typer.Option("--debate-id", help="Debate UUID")],
    target_id: Annotated[str, typer.Option("--target-id", help="Target argument UUID")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Path to content file")] = None,
    content: Annotated[str | None, typer.Option("--content", help="Inline content")] = None,
    stdin: Annotated[bool, typer.Option("--stdin", help="Read content from stdin")] = False,
    client_request_id: Annotated[str | None, typer.Option("--client-request-id", help="Idempotency key")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """Request debate completion (submit RESOLUTION)."""
    arg_content = _read_content(file, content, stdin, fmt)
    if arg_content is None:
        raise typer.Exit(code=4)

    req_id = client_request_id or str(uuid.uuid4())

    try:
        client = _get_client()
        resp = client.post(
            f"/debates/{debate_id}/resolution",
            json={
                "target_id": target_id,
                "content": arg_content,
                "client_request_id": req_id,
            },
        )
    except HTTPClientError as e:
        _handle_server_error(e, fmt)

    data = resp.get("data", {})
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=data)],
        metadata={"message": "Resolution submitted", "client_request_id": req_id},
    )
    _output(response, fmt)


@app.command()
def ruling(
    debate_id: Annotated[str, typer.Option("--debate-id", help="Debate UUID")],
    file: Annotated[Path | None, typer.Option("--file", "-f", help="Path to content file")] = None,
    content: Annotated[str | None, typer.Option("--content", help="Inline content")] = None,
    stdin: Annotated[bool, typer.Option("--stdin", help="Read content from stdin")] = False,
    close: Annotated[bool, typer.Option("--close", help="Close debate after ruling")] = False,
    client_request_id: Annotated[str | None, typer.Option("--client-request-id", help="Idempotency key")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """
    Submit a RULING as Arbitrator (DEV-ONLY).
    
    ⚠️ DEV-ONLY: This command is for testing before Web UI is available.
    """
    ruling_content = _read_content(file, content, stdin, fmt)
    if ruling_content is None:
        raise typer.Exit(code=4)

    body: dict[str, Any] = {"content": ruling_content}
    if close:
        body["close"] = True
    if client_request_id:
        body["client_request_id"] = client_request_id

    try:
        client = _get_client()
        resp = client.post(f"/debates/{debate_id}/ruling", json=body)
    except HTTPClientError as e:
        _handle_server_error(e, fmt)

    data = resp.get("data", {})
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=data)],
        metadata={"message": "Ruling submitted", "closed": close},
    )
    _output(response, fmt)


@app.command()
def intervention(
    debate_id: Annotated[str, typer.Option("--debate-id", help="Debate UUID")],
    client_request_id: Annotated[str | None, typer.Option("--client-request-id", help="Idempotency key")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """
    Submit an INTERVENTION as Arbitrator (DEV-ONLY).
    
    ⚠️ DEV-ONLY: This command is for testing before Web UI is available.
    """
    body: dict[str, Any] = {}
    if client_request_id:
        body["client_request_id"] = client_request_id

    try:
        client = _get_client()
        resp = client.post(f"/debates/{debate_id}/intervention", json=body)
    except HTTPClientError as e:
        _handle_server_error(e, fmt)

    data = resp.get("data", {})
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data=data)],
        metadata={"message": "Intervention submitted"},
    )
    _output(response, fmt)


@app.command("list")
def list_debates(
    state: Annotated[str | None, typer.Option("--state", help="Filter by state")] = None,
    limit: Annotated[int | None, typer.Option("--limit", "-l", help="Max results")] = None,
    offset: Annotated[int | None, typer.Option("--offset", help="Pagination offset")] = None,
    fmt: Annotated[OutputFormat, typer.Option("--format", help="Output format")] = OutputFormat.json,
) -> None:
    """List all debates."""
    try:
        client = _get_client()
        params: dict[str, str] = {}
        if state:
            params["state"] = state
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)
        resp = client.get("/debates", params=params or None)
    except HTTPClientError as e:
        _handle_server_error(e, fmt)

    data = resp.get("data", {})
    total = data.get("total", 0)
    debates = data.get("debates", [])

    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data={"debates": debates})],
        total_count=total,
        has_more=limit is not None and len(debates) == limit,
    )
    _output(response, fmt)


if __name__ == "__main__":
    app()
