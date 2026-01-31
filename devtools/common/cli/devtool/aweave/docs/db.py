"""SQLite-backed document store with immutable version history."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1"


def get_db_path() -> Path:
    if env_path := os.environ.get("AWEAVE_DB_PATH"):
        return Path(env_path)

    db_dir = Path.home() / ".aweave"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "docstore.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS document_versions (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            content TEXT NOT NULL,
            version INTEGER NOT NULL,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            deleted_at TEXT DEFAULT NULL,
            UNIQUE(document_id, version)
        );

        CREATE INDEX IF NOT EXISTS idx_doc_id ON document_versions(document_id);
        CREATE INDEX IF NOT EXISTS idx_doc_latest ON document_versions(document_id, version DESC);
        CREATE INDEX IF NOT EXISTS idx_created_at ON document_versions(created_at DESC);
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_active ON document_versions(document_id) WHERE deleted_at IS NULL"
    )
    conn.execute(
        "INSERT OR IGNORE INTO schema_meta (key, value) VALUES (?, ?)",
        ("version", SCHEMA_VERSION),
    )
    conn.commit()
    return conn


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _document_is_active(conn: sqlite3.Connection, document_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM document_versions WHERE document_id = ? AND deleted_at IS NULL LIMIT 1",
        (document_id,),
    ).fetchone()
    return row is not None


def create_document(summary: str, content: str, metadata: dict[str, Any]) -> dict[str, Any]:
    document_id = str(uuid.uuid4())
    version_id = str(uuid.uuid4())

    with _connect() as conn:
        conn.execute(
            """INSERT INTO document_versions
            (id, document_id, summary, content, version, metadata, created_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)""",
            (
                version_id,
                document_id,
                summary,
                content,
                json.dumps(metadata),
                _utc_now_iso(),
            ),
        )
        conn.commit()

    return {"document_id": document_id, "version": 1, "id": version_id}


def submit_version(
    document_id: str,
    summary: str,
    content: str,
    metadata: dict[str, Any],
) -> dict[str, Any] | None:
    max_retries = 3

    for attempt in range(max_retries):
        try:
            with _connect() as conn:
                conn.execute("BEGIN IMMEDIATE")

                if not _document_is_active(conn, document_id):
                    conn.rollback()
                    return None

                next_version = conn.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM document_versions WHERE document_id = ?",
                    (document_id,),
                ).fetchone()[0]

                version_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO document_versions
                    (id, document_id, summary, content, version, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        version_id,
                        document_id,
                        summary,
                        content,
                        next_version,
                        json.dumps(metadata),
                        _utc_now_iso(),
                    ),
                )
                conn.commit()
                return {"document_id": document_id, "version": next_version, "id": version_id}
        except sqlite3.IntegrityError:
            if attempt < max_retries - 1:
                continue
            raise
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                continue
            raise

    raise RuntimeError("Failed to submit new version after retries")


def get_document(document_id: str, version: int | None = None) -> dict[str, Any] | None:
    with _connect() as conn:
        if version is None:
            row = conn.execute(
                """SELECT * FROM document_versions
                WHERE document_id = ? AND deleted_at IS NULL
                ORDER BY version DESC
                LIMIT 1""",
                (document_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """SELECT * FROM document_versions
                WHERE document_id = ? AND version = ? AND deleted_at IS NULL
                LIMIT 1""",
                (document_id, version),
            ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "document_id": row["document_id"],
        "summary": row["summary"],
        "content": row["content"],
        "version": row["version"],
        "metadata": json.loads(row["metadata"] or "{}"),
        "created_at": row["created_at"],
        "deleted_at": row["deleted_at"],
    }


def list_documents(
    limit: int | None = None,
    include_deleted: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    inner_filter = "" if include_deleted else "WHERE deleted_at IS NULL"

    query = f"""
        SELECT dv.* FROM document_versions dv
        INNER JOIN (
            SELECT document_id, MAX(version) AS max_version
            FROM document_versions {inner_filter}
            GROUP BY document_id
        ) latest
        ON dv.document_id = latest.document_id AND dv.version = latest.max_version
        ORDER BY dv.created_at DESC
    """

    if limit is not None:
        query = f"{query} LIMIT ?"
        params: tuple[Any, ...] = (limit,)
    else:
        params = ()

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
        if include_deleted:
            total = conn.execute("SELECT COUNT(DISTINCT document_id) FROM document_versions").fetchone()[0]
        else:
            total = conn.execute(
                "SELECT COUNT(DISTINCT document_id) FROM document_versions WHERE deleted_at IS NULL"
            ).fetchone()[0]

    documents: list[dict[str, Any]] = []
    for row in rows:
        documents.append(
            {
                "document_id": row["document_id"],
                "summary": row["summary"],
                "version": row["version"],
                "created_at": row["created_at"],
                "deleted_at": row["deleted_at"],
            }
        )

    return documents, total


def get_history(document_id: str, limit: int | None = None) -> tuple[list[dict[str, Any]], int]:
    query = (
        "SELECT id, version, summary, created_at FROM document_versions "
        "WHERE document_id = ? AND deleted_at IS NULL "
        "ORDER BY version DESC"
    )

    if limit is not None:
        query = f"{query} LIMIT ?"
        params: tuple[Any, ...] = (document_id, limit)
    else:
        params = (document_id,)

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM document_versions WHERE document_id = ? AND deleted_at IS NULL",
            (document_id,),
        ).fetchone()[0]

    versions: list[dict[str, Any]] = []
    for row in rows:
        versions.append(
            {
                "id": row["id"],
                "version": row["version"],
                "summary": row["summary"],
                "created_at": row["created_at"],
            }
        )

    return versions, total


def soft_delete_document(document_id: str) -> int:
    deleted_at = _utc_now_iso()

    with _connect() as conn:
        cursor = conn.execute(
            """UPDATE document_versions
            SET deleted_at = ?
            WHERE document_id = ? AND deleted_at IS NULL""",
            (deleted_at, document_id),
        )
        conn.commit()
        return cursor.rowcount
