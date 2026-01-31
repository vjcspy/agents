import type http from 'node:http';
import { WebSocket, WebSocketServer } from 'ws';

import type { Argument, Debate } from './types.js';
import { config } from './config.js';

type ServerToClientMessage =
  | { event: 'initial_state'; data: { debate: Debate; arguments: Argument[] } }
  | { event: 'new_argument'; data: { debate: Debate; argument: Argument } };

type ClientToServerMessage =
  | { event: 'submit_intervention'; data: { debate_id: string; content?: string } }
  | { event: 'submit_ruling'; data: { debate_id: string; content: string; close?: boolean } };

export class WebsocketHub {
  private readonly clientsByDebateId = new Map<string, Set<WebSocket>>();

  constructor(
    private readonly handlers: {
      getInitialState: (debateId: string) => { debate: Debate; arguments: Argument[] };
      submitIntervention: (input: { debate_id: string; content?: string }) => Promise<void>;
      submitRuling: (input: { debate_id: string; content: string; close?: boolean }) => Promise<void>;
    }
  ) {}

  attach(server: http.Server): void {
    const wss = new WebSocketServer({ noServer: true });

    server.on('upgrade', (req, socket, head) => {
      const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
      if (url.pathname !== '/ws') {
        socket.destroy();
        return;
      }

      if (config.authToken) {
        const token = url.searchParams.get('token');
        if (!token || token !== config.authToken) {
          socket.destroy();
          return;
        }
      }

      wss.handleUpgrade(req, socket, head, (ws) => {
        wss.emit('connection', ws, req);
      });
    });

    wss.on('connection', (ws, req) => {
      const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
      const debateId = url.searchParams.get('debate_id');
      if (!debateId) {
        ws.close();
        return;
      }

      this.subscribe(debateId, ws);

      try {
        const initial = this.handlers.getInitialState(debateId);
        this.send(ws, { event: 'initial_state', data: initial });
      } catch {
        ws.close();
        return;
      }

      ws.on('message', async (raw) => {
        try {
          const msg = JSON.parse(raw.toString()) as ClientToServerMessage;
          if (msg.event === 'submit_intervention') {
            await this.handlers.submitIntervention(msg.data);
            return;
          }
          if (msg.event === 'submit_ruling') {
            await this.handlers.submitRuling(msg.data);
            return;
          }
        } catch {
          return;
        }
      });

      ws.on('close', () => this.unsubscribe(debateId, ws));
      ws.on('error', () => this.unsubscribe(debateId, ws));
    });
  }

  broadcastNewArgument(debateId: string, debate: Debate, argument: Argument): void {
    const clients = this.clientsByDebateId.get(debateId);
    if (!clients || clients.size === 0) return;
    const payload: ServerToClientMessage = { event: 'new_argument', data: { debate, argument } };
    for (const ws of clients) {
      if (ws.readyState !== WebSocket.OPEN) continue;
      this.send(ws, payload);
    }
  }

  private subscribe(debateId: string, ws: WebSocket): void {
    const existing = this.clientsByDebateId.get(debateId);
    if (existing) {
      existing.add(ws);
      return;
    }
    this.clientsByDebateId.set(debateId, new Set([ws]));
  }

  private unsubscribe(debateId: string, ws: WebSocket): void {
    const set = this.clientsByDebateId.get(debateId);
    if (!set) return;
    set.delete(ws);
    if (set.size === 0) this.clientsByDebateId.delete(debateId);
  }

  private send(ws: WebSocket, message: ServerToClientMessage): void {
    try {
      ws.send(JSON.stringify(message));
    } catch {
      return;
    }
  }
}
