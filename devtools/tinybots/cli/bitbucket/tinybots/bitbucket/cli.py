"""TinyBots Bitbucket CLI commands."""

import os
from enum import Enum
from typing import Annotated

import typer

from .client import BitbucketClient

app = typer.Typer(help="TinyBots Bitbucket tools")


class OutputFormat(str, Enum):
    """Output format options."""

    json = "json"
    markdown = "markdown"


def _get_client(workspace: str) -> BitbucketClient:
    """Create Bitbucket client from environment variables."""
    username = os.environ.get("BITBUCKET_USER")
    password = os.environ.get("BITBUCKET_APP_PASSWORD")

    if not username or not password:
        typer.echo(
            "Error: BITBUCKET_USER and BITBUCKET_APP_PASSWORD environment variables required.",
            err=True,
        )
        raise typer.Exit(code=1)

    return BitbucketClient(workspace, username, password)


def _output(response, fmt: OutputFormat) -> None:
    """Output response in specified format."""
    if fmt == OutputFormat.json:
        typer.echo(response.to_json())
    else:
        typer.echo(response.to_markdown())


# --- Commands ---


@app.command("pr")
def get_pr(
    repo: Annotated[str, typer.Argument(help="Repository slug")],
    pr_id: Annotated[int, typer.Argument(help="Pull request ID")],
    workspace: Annotated[
        str, typer.Option("--workspace", "-w", help="Bitbucket workspace")
    ] = "tinybots",
    fmt: Annotated[
        OutputFormat, typer.Option("--format", "-f", help="Output format")
    ] = OutputFormat.json,
) -> None:
    """Get pull request details."""
    client = _get_client(workspace)
    response = client.get_pr(repo, pr_id)
    _output(response, fmt)


@app.command("comments")
def list_comments(
    repo: Annotated[str, typer.Argument(help="Repository slug")],
    pr_id: Annotated[int, typer.Argument(help="Pull request ID")],
    workspace: Annotated[
        str, typer.Option("--workspace", "-w", help="Bitbucket workspace")
    ] = "tinybots",
    fmt: Annotated[
        OutputFormat, typer.Option("--format", "-f", help="Output format")
    ] = OutputFormat.json,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max items to return")] = 25,
    offset: Annotated[int, typer.Option("--offset", "-o", help="Offset for pagination")] = 0,
) -> None:
    """List PR comments."""
    client = _get_client(workspace)
    response = client.list_pr_comments(repo, pr_id, limit=limit, offset=offset)
    _output(response, fmt)


@app.command("tasks")
def list_tasks(
    repo: Annotated[str, typer.Argument(help="Repository slug")],
    pr_id: Annotated[int, typer.Argument(help="Pull request ID")],
    workspace: Annotated[
        str, typer.Option("--workspace", "-w", help="Bitbucket workspace")
    ] = "tinybots",
    fmt: Annotated[
        OutputFormat, typer.Option("--format", "-f", help="Output format")
    ] = OutputFormat.json,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max items to return")] = 25,
    offset: Annotated[int, typer.Option("--offset", "-o", help="Offset for pagination")] = 0,
) -> None:
    """List PR tasks."""
    client = _get_client(workspace)
    response = client.list_pr_tasks(repo, pr_id, limit=limit, offset=offset)
    _output(response, fmt)


if __name__ == "__main__":
    app()
