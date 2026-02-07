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

export interface SuccessResponse<T = unknown> {
  success: true;
  data: T;
}

export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    suggestion?: string;
    current_state?: string;
    allowed_roles?: string[];
    [key: string]: unknown;
  };
}
