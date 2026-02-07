import type { ArgumentType, DebateState, Role } from './types';

export type Action =
  | 'create_motion'
  | 'submit_claim'
  | 'submit_appeal'
  | 'submit_resolution'
  | 'submit_ruling'
  | 'submit_intervention';

export function isActionAllowed(
  state: DebateState,
  role: Role,
  action: Action,
): boolean {
  return getAllowedActions(state, role).has(action);
}

function getAllowedActions(state: DebateState, role: Role): Set<Action> {
  if (state === 'CLOSED') return new Set();

  if (state === 'AWAITING_OPPONENT') {
    if (role === 'opponent') return new Set(['submit_claim']);
    if (role === 'arbitrator') return new Set(['submit_intervention']);
    return new Set();
  }

  if (state === 'AWAITING_PROPOSER') {
    if (role === 'proposer')
      return new Set(['submit_claim', 'submit_appeal', 'submit_resolution']);
    if (role === 'arbitrator') return new Set(['submit_intervention']);
    return new Set();
  }

  if (state === 'AWAITING_ARBITRATOR') {
    if (role === 'arbitrator') return new Set(['submit_ruling']);
    return new Set();
  }

  if (state === 'INTERVENTION_PENDING') {
    if (role === 'arbitrator') return new Set(['submit_ruling']);
    return new Set();
  }

  return new Set();
}

export function calculateNextState(
  currentState: DebateState,
  argType: ArgumentType,
  argRole: Role,
  options?: { close?: boolean },
): DebateState {
  if (currentState === 'CLOSED') return 'CLOSED';

  if (argType === 'MOTION' && argRole === 'proposer') return 'AWAITING_OPPONENT';

  if (argType === 'CLAIM') {
    if (argRole === 'opponent') return 'AWAITING_PROPOSER';
    if (argRole === 'proposer') return 'AWAITING_OPPONENT';
  }

  if (argType === 'APPEAL' && argRole === 'proposer')
    return 'AWAITING_ARBITRATOR';
  if (argType === 'RESOLUTION' && argRole === 'proposer')
    return 'AWAITING_ARBITRATOR';

  if (argType === 'INTERVENTION' && argRole === 'arbitrator')
    return 'INTERVENTION_PENDING';

  if (argType === 'RULING' && argRole === 'arbitrator') {
    if (options?.close) return 'CLOSED';
    return 'AWAITING_PROPOSER';
  }

  return currentState;
}
