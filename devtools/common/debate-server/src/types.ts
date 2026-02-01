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

export type WaiterRole = 'proposer' | 'opponent';

export type WaitAction =
  | 'respond'
  | 'align_to_ruling'
  | 'wait_for_proposer'
  | 'wait_for_ruling'
  | 'debate_closed';

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

export type SuccessResponse<T> = {
  success: true;
  data: T;
};

// Error envelope with flat fields (no nested details)
export type ErrorEnvelope = {
  code: string;
  message: string;
  suggestion?: string;
  // ActionNotAllowedError specific fields (flat)
  current_state?: string;
  allowed_roles?: string[];
  // Other context fields can be added flat
  [key: string]: unknown;
};

export type ErrorResponse = {
  success: false;
  error: ErrorEnvelope;
};

export type WaitResponse =
  | {
      has_new_argument: false;
      debate_id: string;
      last_seen_seq: number;
    }
  | {
      has_new_argument: true;
      action: WaitAction;
      debate_state: DebateState;
      argument: Argument;
    };

