# Implementation Plan: Bitbucket CLI với MCP-style Response

**Date:** 2026-01-30  
**Status:** Draft  
**Related:** `devdocs/agent/commands/tinybots/fix-pr-comments.md`

## 1. Overview

**Mục tiêu:** Implement Bitbucket API client trong `devtools/tinybots/cli/bitbucket` với response format theo chuẩn MCP để:

- Thay thế curl commands bằng Python API calls
- Response data chuẩn hóa cho AI agent dễ xử lý
- Code reusable cho các dự án khác

**Reference:**
- MCP Best Practices: `devdocs/agent/skills/common/mcp-builder/reference/mcp_best_practices.md`
- Current command: `devdocs/agent/commands/tinybots/fix-pr-comments.md`

---

## 2. Architecture

```
devtools/
├── common/cli/devtool/aweave/
│   ├── http/                       # [NEW] Shared HTTP utilities
│   │   ├── __init__.py
│   │   ├── client.py              # Base HTTP client với retry, timeout
│   │   └── auth.py                # Authentication strategies (Basic, Bearer, etc.)
│   │
│   └── mcp/                        # [NEW] MCP-style response models
│       ├── __init__.py
│       ├── response.py            # MCPResponse, MCPError, MCPContent
│       └── pagination.py          # Pagination helpers
│
└── tinybots/cli/bitbucket/
    ├── pyproject.toml
    ├── ruff.toml
    └── tinybots/                   # Namespace package
        ├── __init__.py
        └── bitbucket/              # [NEW] Bitbucket module
            ├── __init__.py
            ├── cli.py             # Typer CLI commands
            ├── client.py          # Bitbucket API client
            └── models.py          # Bitbucket data models (PR, Comment, Task)
```

---

## 3. Implementation Tasks

### Phase 1: Common HTTP & MCP Utilities (Reusable)

#### Task 1.1: Create MCP Response Models

**File:** `devtools/common/cli/devtool/aweave/mcp/response.py`

```python
from dataclasses import dataclass, field
from typing import Any, Literal
from enum import Enum
import json

class ContentType(str, Enum):
    TEXT = "text"
    JSON = "json"

@dataclass
class MCPContent:
    """MCP-style content block."""
    type: ContentType
    text: str | None = None
    data: dict[str, Any] | None = None  # For JSON type
    
    def to_dict(self) -> dict[str, Any]:
        result = {"type": self.type.value}
        if self.text is not None:
            result["text"] = self.text
        if self.data is not None:
            result["data"] = self.data
        return result

@dataclass
class MCPError:
    """MCP-style error with actionable message."""
    code: str
    message: str
    suggestion: str | None = None  # Actionable next step
    
    def to_dict(self) -> dict[str, Any]:
        result = {"code": self.code, "message": self.message}
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result

@dataclass
class MCPResponse:
    """
    MCP-inspired response format for CLI tools.
    Designed for both human readability and AI agent processing.
    """
    success: bool
    content: list[MCPContent] = field(default_factory=list)
    error: MCPError | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Pagination support
    has_more: bool = False
    next_offset: int | None = None
    total_count: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        result: dict[str, Any] = {"success": self.success}
        
        if self.content:
            result["content"] = [c.to_dict() for c in self.content]
        
        if self.error:
            result["error"] = self.error.to_dict()
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        # Pagination
        if self.has_more or self.total_count is not None:
            result["has_more"] = self.has_more
            if self.next_offset is not None:
                result["next_offset"] = self.next_offset
            if self.total_count is not None:
                result["total_count"] = self.total_count
                
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def to_markdown(self) -> str:
        """Format as human-readable markdown."""
        lines = []
        
        if not self.success and self.error:
            lines.append(f"## ❌ Error: {self.error.code}")
            lines.append(f"\n{self.error.message}")
            if self.error.suggestion:
                lines.append(f"\n**Suggestion:** {self.error.suggestion}")
            return "\n".join(lines)
        
        for item in self.content:
            if item.type == ContentType.TEXT:
                lines.append(item.text or "")
            elif item.type == ContentType.JSON and item.data:
                lines.append(f"```json\n{json.dumps(item.data, indent=2, default=str)}\n```")
        
        if self.has_more:
            lines.append(f"\n---\n*Showing {len(self.content)} of {self.total_count} items. Use --offset {self.next_offset} to see more.*")
        
        return "\n".join(lines)
```

#### Task 1.2: Create Pagination Utilities

**File:** `devtools/common/cli/devtool/aweave/mcp/pagination.py`

```python
from dataclasses import dataclass
from typing import Any, Callable, TypeVar
from .response import MCPResponse, MCPContent

T = TypeVar("T")

@dataclass
class PaginationParams:
    """Standard pagination parameters."""
    limit: int = 25
    offset: int = 0

def create_paginated_response(
    items: list[T],
    total: int,
    params: PaginationParams,
    formatter: Callable[[T], MCPContent],
    metadata: dict[str, Any] | None = None,
) -> MCPResponse:
    """Create MCP response with pagination metadata."""
    content = [formatter(item) for item in items]
    has_more = params.offset + len(items) < total
    next_offset = params.offset + len(items) if has_more else None
    
    return MCPResponse(
        success=True,
        content=content,
        metadata=metadata or {},
        has_more=has_more,
        next_offset=next_offset,
        total_count=total,
    )
```

#### Task 1.3: Create MCP Package Init

**File:** `devtools/common/cli/devtool/aweave/mcp/__init__.py`

```python
"""MCP-style response utilities for CLI tools."""

from .response import MCPResponse, MCPContent, MCPError, ContentType
from .pagination import PaginationParams, create_paginated_response

__all__ = [
    "MCPResponse",
    "MCPContent", 
    "MCPError",
    "ContentType",
    "PaginationParams",
    "create_paginated_response",
]
```

#### Task 1.4: Create Base HTTP Client

**File:** `devtools/common/cli/devtool/aweave/http/client.py`

```python
from typing import Any
import httpx
from ..mcp.response import MCPResponse, MCPContent, MCPError, ContentType

class HTTPClientError(Exception):
    """HTTP client error."""
    def __init__(self, code: str, message: str, suggestion: str | None = None):
        self.code = code
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)

class HTTPClient:
    """Base HTTP client with retry, timeout, and MCP-formatted responses."""
    
    def __init__(
        self,
        base_url: str,
        auth: tuple[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._auth = auth
        self._headers = headers or {}
        self._timeout = timeout
    
    def _build_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self._base_url,
            auth=self._auth,
            headers=self._headers,
            timeout=self._timeout,
        )
    
    def get(
        self, 
        path: str, 
        params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        GET request, returns raw JSON response.
        Raises HTTPClientError on failure.
        """
        with self._build_client() as client:
            response = client.get(path, params=params)
            return self._handle_response(response)
    
    def post(
        self, 
        path: str, 
        json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """POST request, returns raw JSON response."""
        with self._build_client() as client:
            response = client.post(path, json=json)
            return self._handle_response(response)
    
    def put(
        self, 
        path: str, 
        json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """PUT request, returns raw JSON response."""
        with self._build_client() as client:
            response = client.put(path, json=json)
            return self._handle_response(response)
    
    def delete(self, path: str) -> dict[str, Any]:
        """DELETE request, returns raw JSON response."""
        with self._build_client() as client:
            response = client.delete(path)
            return self._handle_response(response)
    
    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle HTTP response, raise on error."""
        if response.status_code == 401:
            raise HTTPClientError(
                code="AUTH_FAILED",
                message="Authentication failed",
                suggestion="Check your credentials (username/password or token)"
            )
        
        if response.status_code == 403:
            raise HTTPClientError(
                code="FORBIDDEN",
                message="Access denied",
                suggestion="Check if you have the required permissions"
            )
        
        if response.status_code == 404:
            raise HTTPClientError(
                code="NOT_FOUND",
                message="Resource not found",
                suggestion="Verify the resource ID/path is correct"
            )
        
        if response.status_code >= 400:
            raise HTTPClientError(
                code=f"HTTP_{response.status_code}",
                message=f"Request failed: {response.text}",
            )
        
        if response.status_code == 204:
            return {}
        
        return response.json()
```

#### Task 1.5: Create HTTP Package Init

**File:** `devtools/common/cli/devtool/aweave/http/__init__.py`

```python
"""HTTP client utilities."""

from .client import HTTPClient, HTTPClientError

__all__ = ["HTTPClient", "HTTPClientError"]
```

---

### Phase 2: Bitbucket Client Implementation

#### Task 2.1: Create Bitbucket Data Models

**File:** `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/models.py`

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

class TaskState(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"

class PRState(str, Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"
    DECLINED = "DECLINED"
    SUPERSEDED = "SUPERSEDED"

@dataclass
class BitbucketUser:
    """Bitbucket user info."""
    uuid: str
    display_name: str
    account_id: str | None = None
    
    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "BitbucketUser":
        return cls(
            uuid=data.get("uuid", ""),
            display_name=data.get("display_name", "Unknown"),
            account_id=data.get("account_id"),
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "uuid": self.uuid,
            "display_name": self.display_name,
            "account_id": self.account_id,
        }

@dataclass
class PRComment:
    """Pull request comment."""
    id: int
    content: str
    author: BitbucketUser
    file_path: str | None = None
    line: int | None = None
    created_on: datetime | None = None
    
    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "PRComment":
        inline = data.get("inline", {})
        return cls(
            id=data.get("id", 0),
            content=data.get("content", {}).get("raw", ""),
            author=BitbucketUser.from_api(data.get("user", {})),
            file_path=inline.get("path"),
            line=inline.get("to"),
            created_on=datetime.fromisoformat(data["created_on"].replace("Z", "+00:00")) 
                if data.get("created_on") else None,
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "author": self.author.to_dict(),
            "file_path": self.file_path,
            "line": self.line,
            "created_on": self.created_on.isoformat() if self.created_on else None,
        }

@dataclass
class PRTask:
    """Pull request task."""
    id: int
    content: str
    state: TaskState
    comment_id: int | None = None
    creator: BitbucketUser | None = None
    
    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "PRTask":
        comment = data.get("comment", {})
        return cls(
            id=data.get("id", 0),
            content=data.get("content", {}).get("raw", ""),
            state=TaskState(data.get("state", "UNRESOLVED")),
            comment_id=comment.get("id") if comment else None,
            creator=BitbucketUser.from_api(data["creator"]) if data.get("creator") else None,
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "state": self.state.value,
            "comment_id": self.comment_id,
            "creator": self.creator.to_dict() if self.creator else None,
        }

@dataclass
class PullRequest:
    """Pull request info."""
    id: int
    title: str
    description: str | None
    author: BitbucketUser
    source_branch: str
    destination_branch: str
    state: PRState
    created_on: datetime | None = None
    
    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "PullRequest":
        return cls(
            id=data.get("id", 0),
            title=data.get("title", ""),
            description=data.get("description", ""),
            author=BitbucketUser.from_api(data.get("author", {})),
            source_branch=data.get("source", {}).get("branch", {}).get("name", ""),
            destination_branch=data.get("destination", {}).get("branch", {}).get("name", ""),
            state=PRState(data.get("state", "OPEN")),
            created_on=datetime.fromisoformat(data["created_on"].replace("Z", "+00:00"))
                if data.get("created_on") else None,
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "author": self.author.to_dict(),
            "source_branch": self.source_branch,
            "destination_branch": self.destination_branch,
            "state": self.state.value,
            "created_on": self.created_on.isoformat() if self.created_on else None,
        }
```

#### Task 2.2: Create Bitbucket API Client

**File:** `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/client.py`

```python
from typing import Any
from aweave.http import HTTPClient, HTTPClientError
from aweave.mcp import (
    MCPResponse, 
    MCPContent, 
    MCPError, 
    ContentType,
    PaginationParams,
    create_paginated_response,
)
from .models import PullRequest, PRComment, PRTask

class BitbucketClient:
    """Bitbucket API client with MCP-style responses."""
    
    BASE_URL = "https://api.bitbucket.org/2.0"
    
    def __init__(self, workspace: str, username: str, app_password: str):
        self._workspace = workspace
        self._http = HTTPClient(
            base_url=self.BASE_URL,
            auth=(username, app_password),
            headers={"Accept": "application/json"},
        )
    
    def _repo_path(self, repo_slug: str) -> str:
        return f"/repositories/{self._workspace}/{repo_slug}"
    
    # === Pull Request Operations ===
    
    def get_pr(self, repo_slug: str, pr_id: int) -> MCPResponse:
        """Get pull request details."""
        try:
            path = f"{self._repo_path(repo_slug)}/pullrequests/{pr_id}"
            data = self._http.get(path)
            pr = PullRequest.from_api(data)
            
            return MCPResponse(
                success=True,
                content=[MCPContent(type=ContentType.JSON, data=pr.to_dict())],
                metadata={
                    "workspace": self._workspace,
                    "repo_slug": repo_slug,
                    "resource_type": "pull_request",
                },
            )
        except HTTPClientError as e:
            return MCPResponse(
                success=False,
                error=MCPError(code=e.code, message=e.message, suggestion=e.suggestion),
            )
    
    def list_pr_comments(
        self,
        repo_slug: str,
        pr_id: int,
        limit: int = 25,
        offset: int = 0,
    ) -> MCPResponse:
        """List PR comments with pagination."""
        try:
            path = f"{self._repo_path(repo_slug)}/pullrequests/{pr_id}/comments"
            params = {"pagelen": limit, "page": (offset // limit) + 1}
            data = self._http.get(path, params=params)
            
            comments = [PRComment.from_api(c) for c in data.get("values", [])]
            total = data.get("size", len(comments))
            
            return create_paginated_response(
                items=comments,
                total=total,
                params=PaginationParams(limit=limit, offset=offset),
                formatter=lambda c: MCPContent(type=ContentType.JSON, data=c.to_dict()),
                metadata={
                    "workspace": self._workspace,
                    "repo_slug": repo_slug,
                    "pr_id": pr_id,
                    "resource_type": "pr_comments",
                },
            )
        except HTTPClientError as e:
            return MCPResponse(
                success=False,
                error=MCPError(code=e.code, message=e.message, suggestion=e.suggestion),
            )
    
    def list_pr_tasks(
        self,
        repo_slug: str,
        pr_id: int,
        limit: int = 25,
        offset: int = 0,
    ) -> MCPResponse:
        """List PR tasks with pagination."""
        try:
            path = f"{self._repo_path(repo_slug)}/pullrequests/{pr_id}/tasks"
            params = {"pagelen": limit, "page": (offset // limit) + 1}
            data = self._http.get(path, params=params)
            
            tasks = [PRTask.from_api(t) for t in data.get("values", [])]
            total = data.get("size", len(tasks))
            
            return create_paginated_response(
                items=tasks,
                total=total,
                params=PaginationParams(limit=limit, offset=offset),
                formatter=lambda t: MCPContent(type=ContentType.JSON, data=t.to_dict()),
                metadata={
                    "workspace": self._workspace,
                    "repo_slug": repo_slug,
                    "pr_id": pr_id,
                    "resource_type": "pr_tasks",
                },
            )
        except HTTPClientError as e:
            return MCPResponse(
                success=False,
                error=MCPError(code=e.code, message=e.message, suggestion=e.suggestion),
            )
```

#### Task 2.3: Create Bitbucket Module Init

**File:** `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/__init__.py`

```python
"""TinyBots Bitbucket tools."""

from .client import BitbucketClient
from .models import PullRequest, PRComment, PRTask, TaskState, PRState

__all__ = [
    "BitbucketClient",
    "PullRequest",
    "PRComment", 
    "PRTask",
    "TaskState",
    "PRState",
]
```

---

### Phase 3: CLI Commands

#### Task 3.1: Update CLI Entry Point

**File:** `devtools/tinybots/cli/bitbucket/tinybots/bitbucket/cli.py`

```python
import os
import typer
from typing import Annotated
from enum import Enum

from .client import BitbucketClient

app = typer.Typer(help="TinyBots Bitbucket tools")

class OutputFormat(str, Enum):
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

def _output(response, fmt: OutputFormat):
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
    workspace: Annotated[str, typer.Option("--workspace", "-w", help="Bitbucket workspace")] = "tinybots",
    fmt: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.json,
):
    """Get pull request details."""
    client = _get_client(workspace)
    response = client.get_pr(repo, pr_id)
    _output(response, fmt)

@app.command("comments")
def list_comments(
    repo: Annotated[str, typer.Argument(help="Repository slug")],
    pr_id: Annotated[int, typer.Argument(help="Pull request ID")],
    workspace: Annotated[str, typer.Option("--workspace", "-w", help="Bitbucket workspace")] = "tinybots",
    fmt: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.json,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max items to return")] = 25,
    offset: Annotated[int, typer.Option("--offset", "-o", help="Offset for pagination")] = 0,
):
    """List PR comments."""
    client = _get_client(workspace)
    response = client.list_pr_comments(repo, pr_id, limit=limit, offset=offset)
    _output(response, fmt)

@app.command("tasks")
def list_tasks(
    repo: Annotated[str, typer.Argument(help="Repository slug")],
    pr_id: Annotated[int, typer.Argument(help="Pull request ID")],
    workspace: Annotated[str, typer.Option("--workspace", "-w", help="Bitbucket workspace")] = "tinybots",
    fmt: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format")] = OutputFormat.json,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max items to return")] = 25,
    offset: Annotated[int, typer.Option("--offset", "-o", help="Offset for pagination")] = 0,
):
    """List PR tasks."""
    client = _get_client(workspace)
    response = client.list_pr_tasks(repo, pr_id, limit=limit, offset=offset)
    _output(response, fmt)

if __name__ == "__main__":
    app()
```

#### Task 3.2: Update tinybots package init

**File:** `devtools/tinybots/cli/bitbucket/tinybots/__init__.py`

```python
"""TinyBots CLI tools namespace package."""
```

---

### Phase 4: Configuration & Integration

#### Task 4.1: Update Common Package Dependencies

**File:** `devtools/common/cli/devtool/pyproject.toml`

Add `httpx` to dependencies:

```toml
[project]
dependencies = [
    "typer>=0.21.1",
    "pyyaml>=6.0",
    "httpx>=0.28.0",  # NEW - HTTP client
]
```

#### Task 4.2: Update Bitbucket Package Configuration

**File:** `devtools/tinybots/cli/bitbucket/pyproject.toml`

```toml
[project]
name = "tinybots-bitbucket"
version = "0.1.0"
description = "TinyBots Bitbucket tools"
requires-python = ">=3.13"
dependencies = [
    "aweave",  # Common utilities
]

[project.entry-points."aw.plugins"]
tinybots-bitbucket = "tinybots.bitbucket.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["tinybots"]

[tool.uv.sources]
aweave = { workspace = true }
```

#### Task 4.3: Update Workspace Root

**File:** `devtools/pyproject.toml`

Ensure `tinybots-bitbucket` is included in workspace sources:

```toml
[tool.uv.sources]
aweave = { workspace = true }
nab-confluence = { workspace = true }
tinybots-bitbucket = { workspace = true }

[project]
dependencies = [
    "typer>=0.21.1",
    "aweave",
    "nab-confluence",
    "tinybots-bitbucket",  # Add if not present
]
```

---

## 4. File Changes Summary

### New Files

| Path | Description |
|------|-------------|
| `common/cli/devtool/aweave/mcp/__init__.py` | MCP module init |
| `common/cli/devtool/aweave/mcp/response.py` | MCP response models |
| `common/cli/devtool/aweave/mcp/pagination.py` | Pagination utilities |
| `common/cli/devtool/aweave/http/__init__.py` | HTTP module init |
| `common/cli/devtool/aweave/http/client.py` | Base HTTP client |
| `tinybots/cli/bitbucket/tinybots/bitbucket/__init__.py` | Bitbucket module init |
| `tinybots/cli/bitbucket/tinybots/bitbucket/cli.py` | CLI commands |
| `tinybots/cli/bitbucket/tinybots/bitbucket/client.py` | Bitbucket API client |
| `tinybots/cli/bitbucket/tinybots/bitbucket/models.py` | Data models |

### Modified Files

| Path | Changes |
|------|---------|
| `common/cli/devtool/pyproject.toml` | Add `httpx` dependency |
| `tinybots/cli/bitbucket/pyproject.toml` | Add `aweave` dependency, update entry point |
| `tinybots/cli/bitbucket/tinybots/__init__.py` | Update to namespace package |
| `pyproject.toml` | Add `tinybots-bitbucket` to sources (if needed) |

### Files to Delete

| Path | Reason |
|------|--------|
| `tinybots/cli/bitbucket/tinybots/cli.py` | Moved to `tinybots/bitbucket/cli.py` |

---

## 5. Example MCP Response Format

### Success Response

```json
{
  "success": true,
  "content": [
    {
      "type": "json",
      "data": {
        "id": 126,
        "title": "feat: add user authentication",
        "author": {
          "display_name": "John Doe",
          "uuid": "{uuid}"
        },
        "source_branch": "feature/auth",
        "destination_branch": "main",
        "state": "OPEN"
      }
    }
  ],
  "metadata": {
    "workspace": "tinybots",
    "repo_slug": "micro-manager",
    "resource_type": "pull_request"
  }
}
```

### Paginated Response

```json
{
  "success": true,
  "content": [
    {"type": "json", "data": {"id": 1, "content": "Fix typo", ...}},
    {"type": "json", "data": {"id": 2, "content": "Add test", ...}}
  ],
  "metadata": {
    "workspace": "tinybots",
    "repo_slug": "micro-manager",
    "pr_id": 126,
    "resource_type": "pr_comments"
  },
  "has_more": true,
  "next_offset": 25,
  "total_count": 42
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Authentication failed",
    "suggestion": "Check your credentials (username/password or token)"
  }
}
```

---

## 6. CLI Usage Examples

```bash
# Get PR info
aw tinybots-bitbucket pr micro-manager 126

# Get PR info in markdown format
aw tinybots-bitbucket pr micro-manager 126 -f markdown

# List comments with pagination
aw tinybots-bitbucket comments micro-manager 126 --limit 50

# List tasks for different workspace
aw tinybots-bitbucket tasks my-repo 42 -w my-workspace

# Pipe to jq for processing
aw tinybots-bitbucket comments micro-manager 126 | jq '.content[].data'
```

---

## 7. Implementation Checklist

| # | Task | Priority | Effort |
|---|------|----------|--------|
| 1.1 | Create MCP Response Models | High | Medium |
| 1.2 | Create Pagination Utilities | High | Low |
| 1.3 | Create MCP Package Init | High | Low |
| 1.4 | Create Base HTTP Client | High | Medium |
| 1.5 | Create HTTP Package Init | High | Low |
| 2.1 | Create Bitbucket Models | High | Medium |
| 2.2 | Create Bitbucket Client | High | Medium |
| 2.3 | Create Bitbucket Module Init | High | Low |
| 3.1 | Create CLI Commands | High | Medium |
| 3.2 | Update tinybots package init | High | Low |
| 4.1 | Update Common Dependencies | High | Low |
| 4.2 | Update Bitbucket pyproject.toml | High | Low |
| 4.3 | Update Workspace Root | Medium | Low |
| - | Delete old cli.py | High | Low |

---

## 8. Future Extensions

1. **More Bitbucket Operations:**
   - Create/resolve tasks
   - Post comments
   - Approve/decline PR
   - Merge PR

2. **Convert to MCP Server:**
   - Code structure ready for MCP server wrapper
   - Add transport layer (stdio/HTTP)

3. **Caching Layer:**
   - Cache repeated requests
   - Configurable TTL

4. **Rate Limiting:**
   - Handle Bitbucket rate limits
   - Automatic retry with backoff
