// Types copied from debate-server/src/types.ts

export type DebateState =
  | 'AWAITING_OPPONENT'
  | 'AWAITING_PROPOSER'
  | 'AWAITING_ARBITRATOR'
  | 'INTERVENTION_PENDING'
  | 'CLOSED';

export type ArgumentType =
  | 'MOTION'
  | 'CLAIM'
  | 'APPEAL'
  | 'RULING'
  | 'INTERVENTION'
  | 'RESOLUTION';

export type Role = 'proposer' | 'opponent' | 'arbitrator';

export type Debate = {
  id: string;
  title: string;
  debate_type: string;
  state: DebateState;
  created_at: string;
  updated_at: string;
};

export type Argument = {
  id: string;
  debate_id: string;
  parent_id: string | null;
  type: ArgumentType;
  role: Role;
  content: string;
  client_request_id: string | null;
  seq: number;
  created_at: string;
};

// WebSocket message types

export type ServerToClientMessage =
  | { event: 'initial_state'; data: { debate: Debate; arguments: Argument[] } }
  | { event: 'new_argument'; data: { debate: Debate; argument: Argument } };

export type ClientToServerMessage =
  | { event: 'submit_intervention'; data: { debate_id: string; content?: string } }
  | { event: 'submit_ruling'; data: { debate_id: string; content: string; close?: boolean } };

// API response types

export type SuccessResponse<T> = {
  success: true;
  data: T;
};

export type ErrorResponse = {
  success: false;
  error: {
    code: string;
    message: string;
    suggestion?: string;
  };
};

export type ApiResponse<T> = SuccessResponse<T> | ErrorResponse;
