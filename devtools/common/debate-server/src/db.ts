import fs from 'node:fs';
import path from 'node:path';

import Database from 'better-sqlite3';

import { config } from './config.js';
import {
  ArgumentNotFoundError,
  DebateNotFoundError,
  InvalidInputError,
  NotFoundError
} from './errors.js';
import type { Argument, Debate, DebateState } from './types.js';

type SqliteDb = Database.Database;

function ensureParentDir(filePath: string): void {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
}

const schemaSql = `
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('version', '1');

CREATE TABLE IF NOT EXISTS debates (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  debate_type TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'AWAITING_OPPONENT',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS arguments (
  id TEXT PRIMARY KEY,
  debate_id TEXT NOT NULL REFERENCES debates(id),
  parent_id TEXT REFERENCES arguments(id),
  type TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  client_request_id TEXT,
  seq INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(debate_id, client_request_id),
  UNIQUE(debate_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_arguments_debate_id ON arguments(debate_id);
CREATE INDEX IF NOT EXISTS idx_arguments_parent_id ON arguments(parent_id);
CREATE INDEX IF NOT EXISTS idx_arguments_seq ON arguments(debate_id, seq);
`;

function isSqliteBusyError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false;
  const code = (err as { code?: unknown }).code;
  return code === 'SQLITE_BUSY' || code === 'SQLITE_BUSY_TIMEOUT';
}

function isSqliteCantOpenError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false;
  const code = (err as { code?: unknown }).code;
  return code === 'SQLITE_CANTOPEN';
}

export class DebateDb {
  private readonly db: SqliteDb;

  constructor(db: SqliteDb) {
    this.db = db;
  }

  initSchema(): void {
    this.db.exec(schemaSql);
  }

  runImmediateTransaction<T>(fn: () => T): T {
    this.db.exec('BEGIN IMMEDIATE;');
    try {
      const result = fn();
      this.db.exec('COMMIT;');
      return result;
    } catch (err) {
      try {
        this.db.exec('ROLLBACK;');
      } catch {}
      throw err;
    }
  }

  getDebate(debateId: string): Debate | null {
    const row = this.db
      .prepare(
        'SELECT id, title, debate_type, state, created_at, updated_at FROM debates WHERE id = ?'
      )
      .get(debateId) as Debate | undefined;
    return row ?? null;
  }

  listDebates(): Debate[] {
    const rows = this.db
      .prepare('SELECT id, title, debate_type, state, created_at, updated_at FROM debates ORDER BY updated_at DESC')
      .all() as Debate[];
    return rows;
  }

  getArgument(argumentId: string): Argument | null {
    const row = this.db
      .prepare(
        'SELECT id, debate_id, parent_id, type, role, content, client_request_id, seq, created_at FROM arguments WHERE id = ?'
      )
      .get(argumentId) as Argument | undefined;
    return row ?? null;
  }

  getLatestArgument(debateId: string): Argument | null {
    const row = this.db
      .prepare(
        'SELECT id, debate_id, parent_id, type, role, content, client_request_id, seq, created_at FROM arguments WHERE debate_id = ? ORDER BY seq DESC LIMIT 1'
      )
      .get(debateId) as Argument | undefined;
    return row ?? null;
  }

  getArguments(debateId: string, limit: number): Argument[] {
    const rows = this.db
      .prepare(
        'SELECT id, debate_id, parent_id, type, role, content, client_request_id, seq, created_at FROM arguments WHERE debate_id = ? ORDER BY seq ASC LIMIT ?'
      )
      .all(debateId, limit) as Argument[];
    return rows;
  }

  getRecentArguments(debateId: string, limit: number): Argument[] {
    const rows = this.db
      .prepare(
        'SELECT id, debate_id, parent_id, type, role, content, client_request_id, seq, created_at FROM arguments WHERE debate_id = ? ORDER BY seq DESC LIMIT ?'
      )
      .all(debateId, limit) as Argument[];
    return rows.reverse();
  }

  findArgumentByClientRequestId(debateId: string, clientRequestId: string): Argument | null {
    const row = this.db
      .prepare(
        'SELECT id, debate_id, parent_id, type, role, content, client_request_id, seq, created_at FROM arguments WHERE debate_id = ? AND client_request_id = ?'
      )
      .get(debateId, clientRequestId) as Argument | undefined;
    return row ?? null;
  }

  getNextSeq(debateId: string): number {
    const row = this.db
      .prepare('SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM arguments WHERE debate_id = ?')
      .get(debateId) as { next_seq: number } | undefined;
    return row?.next_seq ?? 1;
  }

  insertDebate(debate: { id: string; title: string; debate_type: string; state: DebateState }): void {
    this.db
      .prepare('INSERT INTO debates (id, title, debate_type, state) VALUES (?, ?, ?, ?)')
      .run(debate.id, debate.title, debate.debate_type, debate.state);
  }

  updateDebateState(debateId: string, state: DebateState): void {
    this.db
      .prepare("UPDATE debates SET state = ?, updated_at = datetime('now') WHERE id = ?")
      .run(state, debateId);
  }

  insertArgument(argument: Omit<Argument, 'created_at'>): Argument {
    this.db
      .prepare(
        'INSERT INTO arguments (id, debate_id, parent_id, type, role, content, client_request_id, seq) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
      )
      .run(
        argument.id,
        argument.debate_id,
        argument.parent_id,
        argument.type,
        argument.role,
        argument.content,
        argument.client_request_id,
        argument.seq
      );

    const inserted = this.getArgument(argument.id);
    if (!inserted) throw new NotFoundError(`Failed to read inserted argument: ${argument.id}`);
    return inserted;
  }

  validateArgumentBelongsToDebate(debateId: string, argumentId: string): Argument {
    const arg = this.getArgument(argumentId);
    if (!arg) throw new ArgumentNotFoundError(argumentId);
    if (arg.debate_id !== debateId) {
      throw new InvalidInputError('argument_id does not belong to this debate', {
        debate_id: debateId,
        argument_id: argumentId
      });
    }
    return arg;
  }

  ensureDebateExists(debateId: string): Debate {
    const debate = this.getDebate(debateId);
    if (!debate) throw new DebateNotFoundError(debateId);
    return debate;
  }
}

export function createDb(): DebateDb {
  const primaryPath = config.dbPath;
  const fallbackPath = path.join(process.cwd(), '.aweave', 'debate.db');

  try {
    ensureParentDir(primaryPath);
    return new DebateDb(new Database(primaryPath));
  } catch (err) {
    if (!isSqliteCantOpenError(err)) throw err;
    ensureParentDir(fallbackPath);
    return new DebateDb(new Database(fallbackPath));
  }
}

export async function withSqliteBusyRetry<T>(fn: () => T): Promise<T> {
  let attempt = 0;
  while (true) {
    try {
      return fn();
    } catch (err) {
      attempt += 1;
      if (!isSqliteBusyError(err) || attempt > config.sqliteBusyMaxRetries) throw err;
      const delay = config.sqliteBusyBaseDelayMs * Math.pow(2, attempt - 1);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
}
