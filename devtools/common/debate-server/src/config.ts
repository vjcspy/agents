import os from 'node:os';
import path from 'node:path';

function expandHome(filepath: string): string {
  if (filepath.startsWith('~')) {
    return path.join(os.homedir(), filepath.slice(1));
  }
  return filepath;
}

const defaultDbPath = path.join(os.homedir(), '.aweave', 'debate.db');

export const config = {
  host: process.env.DEBATE_SERVER_HOST || '127.0.0.1',
  port: Number.parseInt(process.env.DEBATE_SERVER_PORT || '3456', 10),
  authToken: process.env.DEBATE_AUTH_TOKEN,
  dbPath: expandHome(process.env.DEBATE_DB_PATH || defaultDbPath),
  pollTimeoutMs: Number.parseInt(process.env.DEBATE_POLL_TIMEOUT_MS || '60000', 10),
  // HTTP keep-alive/timeout must be > pollTimeoutMs to ensure long polling works
  httpTimeoutMs: Number.parseInt(process.env.DEBATE_HTTP_TIMEOUT_MS || '65000', 10),
  maxContentLength: Number.parseInt(process.env.DEBATE_MAX_CONTENT_LENGTH || `${10 * 1024}`, 10),
  sqliteBusyMaxRetries: Number.parseInt(process.env.DEBATE_SQLITE_BUSY_MAX_RETRIES || '7', 10),
  sqliteBusyBaseDelayMs: Number.parseInt(process.env.DEBATE_SQLITE_BUSY_BASE_DELAY_MS || '10', 10)
};

