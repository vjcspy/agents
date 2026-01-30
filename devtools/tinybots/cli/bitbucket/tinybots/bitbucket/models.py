"""Bitbucket data models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    """PR task state."""

    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"


class PRState(str, Enum):
    """Pull request state."""

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
        """Create from Bitbucket API response."""
        return cls(
            uuid=data.get("uuid", ""),
            display_name=data.get("display_name", "Unknown"),
            account_id=data.get("account_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
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
        """Create from Bitbucket API response."""
        inline = data.get("inline", {})
        created_on = None
        if data.get("created_on"):
            created_on = datetime.fromisoformat(data["created_on"].replace("Z", "+00:00"))

        return cls(
            id=data.get("id", 0),
            content=data.get("content", {}).get("raw", ""),
            author=BitbucketUser.from_api(data.get("user", {})),
            file_path=inline.get("path"),
            line=inline.get("to"),
            created_on=created_on,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
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
        """Create from Bitbucket API response."""
        comment = data.get("comment", {})
        creator = None
        if data.get("creator"):
            creator = BitbucketUser.from_api(data["creator"])

        return cls(
            id=data.get("id", 0),
            content=data.get("content", {}).get("raw", ""),
            state=TaskState(data.get("state", "UNRESOLVED")),
            comment_id=comment.get("id") if comment else None,
            creator=creator,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
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
        """Create from Bitbucket API response."""
        created_on = None
        if data.get("created_on"):
            created_on = datetime.fromisoformat(data["created_on"].replace("Z", "+00:00"))

        return cls(
            id=data.get("id", 0),
            title=data.get("title", ""),
            description=data.get("description", ""),
            author=BitbucketUser.from_api(data.get("author", {})),
            source_branch=data.get("source", {}).get("branch", {}).get("name", ""),
            destination_branch=data.get("destination", {}).get("branch", {}).get("name", ""),
            state=PRState(data.get("state", "OPEN")),
            created_on=created_on,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
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
