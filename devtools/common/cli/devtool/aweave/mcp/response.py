"""MCP-style response models for CLI tools."""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContentType(str, Enum):
    """MCP content types."""

    TEXT = "text"
    JSON = "json"


@dataclass
class MCPContent:
    """MCP-style content block."""

    type: ContentType
    text: str | None = None
    data: dict[str, Any] | None = None  # For JSON type

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        result: dict[str, Any] = {"type": self.type.value}
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
        """Serialize to dictionary."""
        result: dict[str, Any] = {"code": self.code, "message": self.message}
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
        lines: list[str] = []

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
            if self.total_count is not None:
                msg = f"Showing {len(self.content)} of {self.total_count} items."
            else:
                msg = f"Showing {len(self.content)} items. More available."
            lines.append(
                f"\n---\n*{msg} Use --offset {self.next_offset} to see more.*"
            )

        return "\n".join(lines)
