"""Bitbucket API client with MCP-style responses."""

from aweave.http import HTTPClient, HTTPClientError
from aweave.mcp import (
    ContentType,
    MCPContent,
    MCPError,
    MCPResponse,
    PaginationParams,
    create_paginated_response,
)

from .models import PRComment, PRTask, PullRequest


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
