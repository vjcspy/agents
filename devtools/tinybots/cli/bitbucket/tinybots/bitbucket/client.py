"""Bitbucket API client with MCP-style responses."""

from typing import Any

from aweave.http import HTTPClient, HTTPClientError
from aweave.mcp import (
    ContentType,
    MCPContent,
    MCPError,
    MCPResponse,
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

    def _fetch_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_items: int = 500,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """
        Fetch all pages from a Bitbucket paginated endpoint.

        Args:
            path: API endpoint path
            params: Additional query parameters
            max_items: Maximum items to fetch (safety limit)

        Returns:
            Tuple of (all_items, total_count_if_available)
        """
        all_items: list[dict[str, Any]] = []
        total_count: int | None = None
        params = params or {}
        params["pagelen"] = 100  # Always use max page size for efficiency

        current_url: str | None = None
        first_request = True

        while True:
            if first_request:
                data = self._http.get(path, params=params)
                first_request = False
            else:
                data = self._http.get_url(current_url)

            values = data.get("values", [])
            all_items.extend(values)

            # Get total count if available (first page usually has it)
            if total_count is None:
                total_count = data.get("size")

            # Check if more pages exist
            current_url = data.get("next")
            if not current_url or len(all_items) >= max_items:
                break

        return all_items[:max_items], total_count

    def get_pr(self, repo_slug: str, pr_id: int) -> MCPResponse:
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
        max_items: int = 500,
    ) -> MCPResponse:
        try:
            path = f"{self._repo_path(repo_slug)}/pullrequests/{pr_id}/comments"

            all_comments_data, total_count = self._fetch_all_pages(
                path, max_items=max_items
            )

            comments = [PRComment.from_api(c) for c in all_comments_data]

            return create_paginated_response(
                items=comments,
                total=total_count or len(comments),
                has_more=False,
                next_offset=None,
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
        max_items: int = 500,
    ) -> MCPResponse:
        try:
            path = f"{self._repo_path(repo_slug)}/pullrequests/{pr_id}/tasks"

            all_tasks_data, total_count = self._fetch_all_pages(
                path, max_items=max_items
            )

            tasks = [PRTask.from_api(t) for t in all_tasks_data]

            return create_paginated_response(
                items=tasks,
                total=total_count or len(tasks),
                has_more=False,
                next_offset=None,
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
