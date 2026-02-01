import http from 'node:http';

import { config } from './config.js';
import { createDb } from './db.js';
import { createHttpApp } from './http.js';
import { LockService } from './lockService.js';
import { ArgumentService, DebateService, type Broadcast } from './services.js';
import { WebsocketHub } from './websocket.js';

const db = createDb();
db.initSchema();

const locks = new LockService();

let argumentService: ArgumentService;

const wsHub = new WebsocketHub({
  getInitialState: (debateId: string) => {
    const debate = db.ensureDebateExists(debateId);
    const args = db.getArguments(debateId, 5000);
    return { debate, arguments: args };
  },
  submitIntervention: async (input: { debate_id: string; content?: string }) => {
    await argumentService.submitIntervention(input);
  },
  submitRuling: async (input: { debate_id: string; content: string; close?: boolean }) => {
    await argumentService.submitRuling(input);
  }
});

const broadcast: Broadcast = {
  newArgument: (debateId, argument, debate) => {
    wsHub.broadcastNewArgument(debateId, debate, argument);
  }
};

const debateService = new DebateService(db, locks, broadcast);
argumentService = new ArgumentService(db, locks, broadcast);

const app = createHttpApp({ debate: debateService, argument: argumentService });
const server = http.createServer(app);

// Set HTTP timeout > poll timeout to ensure long polling works
// Express/Node default can be < 60s, causing premature disconnection
server.timeout = config.httpTimeoutMs;
server.keepAliveTimeout = config.httpTimeoutMs;

wsHub.attach(server);

server.listen(config.port, config.host, () => {
  console.log(`debate-server listening on http://${config.host}:${config.port}`);
});
