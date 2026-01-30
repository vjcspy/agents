"""Pagination utilities for MCP responses."""

from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from .response import MCPContent, MCPResponse

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
