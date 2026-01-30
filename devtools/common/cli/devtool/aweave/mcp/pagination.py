"""Pagination utilities for MCP responses."""

from typing import Any, Callable, TypeVar

from .response import MCPContent, MCPResponse

T = TypeVar("T")


def create_paginated_response(
    items: list[T],
    total: int | None,
    has_more: bool,
    next_offset: int | None,
    formatter: Callable[[T], MCPContent],
    metadata: dict[str, Any] | None = None,
) -> MCPResponse:
    content = [formatter(item) for item in items]

    return MCPResponse(
        success=True,
        content=content,
        metadata=metadata or {},
        has_more=has_more,
        next_offset=next_offset,
        total_count=total,
    )
