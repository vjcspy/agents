import crypto from 'node:crypto';

import { config } from './config.js';
import { ActionNotAllowedError, ContentTooLargeError, InvalidInputError } from './errors.js';
import { calculateNextState, isActionAllowed, type Action } from './stateMachine.js';
import type { Argument, Debate, DebateState, Role, WaitAction, WaiterRole } from './types.js';
import { DebateDb, withSqliteBusyRetry } from './db.js';
import { LockService } from './lockService.js';

export type Broadcast = {
  newArgument: (debateId: string, argument: Argument, debate: Debate) => void;
};

function validateContentSize(content: string): void {
  if (content.length > config.maxContentLength) throw new ContentTooLargeError(config.maxContentLength);
}

function toActionNotAllowedError(state: DebateState, role: Role, action: Action): ActionNotAllowedError {
  const allowedRoles: Role[] =
    state === 'AWAITING_OPPONENT'
      ? (['opponent', 'arbitrator'] as Role[])
      : state === 'AWAITING_PROPOSER'
        ? (['proposer', 'arbitrator'] as Role[])
        : state === 'AWAITING_ARBITRATOR' || state === 'INTERVENTION_PENDING'
          ? (['arbitrator'] as Role[])
          : ([] as Role[]);

  const suggestion =
    state === 'CLOSED'
      ? 'This debate is closed'
      : `Wait for ${allowedRoles.join(' or ')} to submit`;

  return new ActionNotAllowedError(`Role '${role}' cannot perform '${action}' in state '${state}'`, {
    current_state: state,
    allowed_roles: allowedRoles,
    suggestion
  });
}

function buildWaitAction(argument: Argument, debateState: DebateState, waiterRole: WaiterRole): WaitAction {
  if (debateState === 'CLOSED') return 'debate_closed';

  const key = `${argument.type}:${argument.role}:${waiterRole}`;

  const map: Record<string, WaitAction> = {
    'CLAIM:opponent:proposer': 'respond',
    'CLAIM:proposer:opponent': 'respond',
    'APPEAL:proposer:proposer': 'wait_for_ruling',
    'APPEAL:proposer:opponent': 'wait_for_ruling',
    'RESOLUTION:proposer:proposer': 'wait_for_ruling',
    'RESOLUTION:proposer:opponent': 'wait_for_ruling',
    'RULING:arbitrator:proposer': 'align_to_ruling',
    'RULING:arbitrator:opponent': 'wait_for_proposer',
    'INTERVENTION:arbitrator:proposer': 'wait_for_ruling',
    'INTERVENTION:arbitrator:opponent': 'wait_for_ruling'
  };

  const action = map[key];
  if (!action) return 'respond';
  return action;
}

export class DebateService {
  constructor(
    private readonly db: DebateDb,
    private readonly locks: LockService,
    private readonly broadcast: Broadcast
  ) {}

  async createDebate(input: {
    debate_id: string;
    title: string;
    debate_type: string;
    motion_content: string;
    client_request_id: string;
  }): Promise<{ debate: Debate; argument: Argument }> {
    validateContentSize(input.motion_content);

    const result = await this.locks.withLock(input.debate_id, async () => {
      return await withSqliteBusyRetry(() => {
        return this.db.runImmediateTransaction(() => {
          const existingDebate = this.db.getDebate(input.debate_id);
          if (existingDebate) {
            const existingMotion = this.db.findArgumentByClientRequestId(
              input.debate_id,
              input.client_request_id
            );
            if (!existingMotion) {
              throw new InvalidInputError('Debate already exists with a different request', {
                debate_id: input.debate_id
              });
            }
            return { debate: existingDebate, argument: existingMotion, isExisting: true };
          }

          const debateRow = {
            id: input.debate_id,
            title: input.title,
            debate_type: input.debate_type,
            state: 'AWAITING_OPPONENT' as DebateState
          };
          this.db.insertDebate(debateRow);

          const motionArg: Omit<Argument, 'created_at'> = {
            id: crypto.randomUUID(),
            debate_id: input.debate_id,
            parent_id: null,
            type: 'MOTION',
            role: 'proposer',
            content: input.motion_content,
            client_request_id: input.client_request_id,
            seq: 1
          };
          const inserted = this.db.insertArgument(motionArg);
          const debate = this.db.ensureDebateExists(input.debate_id);
          return { debate, argument: inserted, isExisting: false };
        });
      });
    });

    if (!(result as { isExisting: boolean }).isExisting) {
      this.locks.notifyNewArgument(input.debate_id);
      this.broadcast.newArgument(input.debate_id, result.argument, result.debate);
    }

    return { debate: result.debate, argument: result.argument };
  }

  getDebate(debateId: string): Debate {
    return this.db.ensureDebateExists(debateId);
  }

  // GET /debates/:id?limit=N
  // motion ALWAYS included (not counted in limit)
  // limit=N returns N most recent arguments (excluding motion)
  // limit=0 returns empty arguments array
  // limit not set returns all arguments
  getDebateWithArgs(
    debateId: string,
    argumentLimit?: number
  ): { debate: Debate; motion: Argument | null; arguments: Argument[] } {
    const debate = this.db.ensureDebateExists(debateId);
    const motion = this.db.getMotion(debateId);

    let args: Argument[];
    if (argumentLimit === undefined) {
      // No limit - return all arguments excluding motion
      args = this.db.getRecentArgumentsExcludingMotion(debateId, 10000);
    } else if (argumentLimit <= 0) {
      args = [];
    } else {
      const limit = Math.min(500, argumentLimit);
      args = this.db.getRecentArgumentsExcludingMotion(debateId, limit);
    }

    return { debate, motion, arguments: args };
  }

  // Legacy method for backward compatibility
  getContext(debateId: string, argumentLimit: number): { debate: Debate; arguments: Argument[] } {
    const debate = this.db.ensureDebateExists(debateId);
    const limit = Math.max(1, Math.min(500, argumentLimit));
    const args = this.db.getRecentArguments(debateId, limit);
    return { debate, arguments: args };
  }

  listDebates(opts?: { state?: string; limit?: number; offset?: number }): { debates: Debate[]; total: number } {
    return this.db.listDebates(opts);
  }

  async waitForResponse(input: {
    debate_id: string;
    argument_id?: string | null;
    role: WaiterRole;
    poll_timeout_ms: number;
  }): Promise<
    | { has_new_argument: false; debate_id: string; last_seen_seq: number }
    | { has_new_argument: true; action: WaitAction; debate_state: DebateState; argument: Argument }
  > {
    this.db.ensureDebateExists(input.debate_id);

    let lastSeenSeq = 0;
    if (input.argument_id) {
      const lastSeenArg = this.db.validateArgumentBelongsToDebate(input.debate_id, input.argument_id);
      lastSeenSeq = lastSeenArg.seq;
    }

    const latest = this.db.getLatestArgument(input.debate_id);
    if (latest && latest.seq > lastSeenSeq) {
      const updatedDebate = this.db.ensureDebateExists(input.debate_id);
      return {
        has_new_argument: true,
        action: buildWaitAction(latest, updatedDebate.state, input.role),
        debate_state: updatedDebate.state,
        argument: latest
      };
    }

    const listenerPromise = this.locks.waitForArgument(input.debate_id, input.poll_timeout_ms);

    const latestAfterAttach = this.db.getLatestArgument(input.debate_id);
    if (latestAfterAttach && latestAfterAttach.seq > lastSeenSeq) {
      const updatedDebate = this.db.ensureDebateExists(input.debate_id);
      return {
        has_new_argument: true,
        action: buildWaitAction(latestAfterAttach, updatedDebate.state, input.role),
        debate_state: updatedDebate.state,
        argument: latestAfterAttach
      };
    }

    const gotSignal = await listenerPromise;
    if (!gotSignal) {
      // Timeout - return debate_id and last_seen_seq for debugging/resume
      return { has_new_argument: false, debate_id: input.debate_id, last_seen_seq: lastSeenSeq };
    }

    const updatedLatest = this.db.getLatestArgument(input.debate_id);
    if (!updatedLatest || updatedLatest.seq <= lastSeenSeq) {
      return { has_new_argument: false, debate_id: input.debate_id, last_seen_seq: lastSeenSeq };
    }
    const updatedDebate = this.db.ensureDebateExists(input.debate_id);
    return {
      has_new_argument: true,
      action: buildWaitAction(updatedLatest, updatedDebate.state, input.role),
      debate_state: updatedDebate.state,
      argument: updatedLatest
    };
  }
}

export class ArgumentService {
  constructor(
    private readonly db: DebateDb,
    private readonly locks: LockService,
    private readonly broadcast: Broadcast
  ) {}

  async submitClaim(input: {
    debate_id: string;
    role: Exclude<Role, 'arbitrator'>;
    target_id: string;
    content: string;
    client_request_id: string;
  }): Promise<{ debate: Debate; argument: Argument }> {
    validateContentSize(input.content);

    const result = await this.locks.withLock(input.debate_id, async () => {
      return await withSqliteBusyRetry(() => {
        return this.db.runImmediateTransaction(() => {
          const debate = this.db.ensureDebateExists(input.debate_id);

          const existing = this.db.findArgumentByClientRequestId(
            input.debate_id,
            input.client_request_id
          );
          if (existing) return { debate, argument: existing, isExisting: true };

          this.db.validateArgumentBelongsToDebate(input.debate_id, input.target_id);

          if (!isActionAllowed(debate.state, input.role, 'submit_claim')) {
            throw toActionNotAllowedError(debate.state, input.role, 'submit_claim');
          }

          const nextSeq = this.db.getNextSeq(input.debate_id);
          const argument: Omit<Argument, 'created_at'> = {
            id: crypto.randomUUID(),
            debate_id: input.debate_id,
            parent_id: input.target_id,
            type: 'CLAIM',
            role: input.role,
            content: input.content,
            client_request_id: input.client_request_id,
            seq: nextSeq
          };

          const inserted = this.db.insertArgument(argument);
          const nextState = calculateNextState(debate.state, 'CLAIM', input.role);
          this.db.updateDebateState(input.debate_id, nextState);
          const updatedDebate = this.db.ensureDebateExists(input.debate_id);
          return { debate: updatedDebate, argument: inserted, isExisting: false };
        });
      });
    });

    if (!(result as { isExisting: boolean }).isExisting) {
      this.locks.notifyNewArgument(input.debate_id);
      this.broadcast.newArgument(input.debate_id, result.argument, result.debate);
    }

    return { debate: result.debate, argument: result.argument };
  }

  async submitAppeal(input: {
    debate_id: string;
    target_id: string;
    content: string;
    client_request_id: string;
  }): Promise<{ debate: Debate; argument: Argument }> {
    validateContentSize(input.content);

    const result = await this.locks.withLock(input.debate_id, async () => {
      return await withSqliteBusyRetry(() => {
        return this.db.runImmediateTransaction(() => {
          const debate = this.db.ensureDebateExists(input.debate_id);

          const existing = this.db.findArgumentByClientRequestId(
            input.debate_id,
            input.client_request_id
          );
          if (existing) return { debate, argument: existing, isExisting: true };

          this.db.validateArgumentBelongsToDebate(input.debate_id, input.target_id);

          if (!isActionAllowed(debate.state, 'proposer', 'submit_appeal')) {
            throw toActionNotAllowedError(debate.state, 'proposer', 'submit_appeal');
          }

          const nextSeq = this.db.getNextSeq(input.debate_id);
          const argument: Omit<Argument, 'created_at'> = {
            id: crypto.randomUUID(),
            debate_id: input.debate_id,
            parent_id: input.target_id,
            type: 'APPEAL',
            role: 'proposer',
            content: input.content,
            client_request_id: input.client_request_id,
            seq: nextSeq
          };

          const inserted = this.db.insertArgument(argument);
          const nextState = calculateNextState(debate.state, 'APPEAL', 'proposer');
          this.db.updateDebateState(input.debate_id, nextState);
          const updatedDebate = this.db.ensureDebateExists(input.debate_id);
          return { debate: updatedDebate, argument: inserted, isExisting: false };
        });
      });
    });

    if (!(result as { isExisting: boolean }).isExisting) {
      this.locks.notifyNewArgument(input.debate_id);
      this.broadcast.newArgument(input.debate_id, result.argument, result.debate);
    }

    return { debate: result.debate, argument: result.argument };
  }

  async submitResolution(input: {
    debate_id: string;
    target_id: string;
    content: string;
    client_request_id: string;
  }): Promise<{ debate: Debate; argument: Argument }> {
    validateContentSize(input.content);

    const result = await this.locks.withLock(input.debate_id, async () => {
      return await withSqliteBusyRetry(() => {
        return this.db.runImmediateTransaction(() => {
          const debate = this.db.ensureDebateExists(input.debate_id);

          const existing = this.db.findArgumentByClientRequestId(
            input.debate_id,
            input.client_request_id
          );
          if (existing) return { debate, argument: existing, isExisting: true };

          this.db.validateArgumentBelongsToDebate(input.debate_id, input.target_id);

          if (!isActionAllowed(debate.state, 'proposer', 'submit_resolution')) {
            throw toActionNotAllowedError(debate.state, 'proposer', 'submit_resolution');
          }

          const nextSeq = this.db.getNextSeq(input.debate_id);
          const argument: Omit<Argument, 'created_at'> = {
            id: crypto.randomUUID(),
            debate_id: input.debate_id,
            parent_id: input.target_id,
            type: 'RESOLUTION',
            role: 'proposer',
            content: input.content,
            client_request_id: input.client_request_id,
            seq: nextSeq
          };

          const inserted = this.db.insertArgument(argument);
          const nextState = calculateNextState(debate.state, 'RESOLUTION', 'proposer');
          this.db.updateDebateState(input.debate_id, nextState);
          const updatedDebate = this.db.ensureDebateExists(input.debate_id);
          return { debate: updatedDebate, argument: inserted, isExisting: false };
        });
      });
    });

    if (!(result as { isExisting: boolean }).isExisting) {
      this.locks.notifyNewArgument(input.debate_id);
      this.broadcast.newArgument(input.debate_id, result.argument, result.debate);
    }

    return { debate: result.debate, argument: result.argument };
  }

  // DEV-ONLY: client_request_id optional for idempotency
  async submitIntervention(input: {
    debate_id: string;
    content?: string | null;
    client_request_id?: string | null;
  }): Promise<{ debate: Debate; argument: Argument }> {
    const content = input.content ?? '';
    validateContentSize(content);

    const result = await this.locks.withLock(input.debate_id, async () => {
      return await withSqliteBusyRetry(() => {
        return this.db.runImmediateTransaction(() => {
          const debate = this.db.ensureDebateExists(input.debate_id);

          // Idempotency check if client_request_id provided
          if (input.client_request_id) {
            const existing = this.db.findArgumentByClientRequestId(
              input.debate_id,
              input.client_request_id
            );
            if (existing) return { debate, argument: existing, isExisting: true };
          }

          if (!isActionAllowed(debate.state, 'arbitrator', 'submit_intervention')) {
            throw toActionNotAllowedError(debate.state, 'arbitrator', 'submit_intervention');
          }

          const nextSeq = this.db.getNextSeq(input.debate_id);
          const argument: Omit<Argument, 'created_at'> = {
            id: crypto.randomUUID(),
            debate_id: input.debate_id,
            parent_id: null,
            type: 'INTERVENTION',
            role: 'arbitrator',
            content,
            client_request_id: input.client_request_id ?? null,
            seq: nextSeq
          };

          const inserted = this.db.insertArgument(argument);
          const nextState = calculateNextState(debate.state, 'INTERVENTION', 'arbitrator');
          this.db.updateDebateState(input.debate_id, nextState);
          const updatedDebate = this.db.ensureDebateExists(input.debate_id);
          return { debate: updatedDebate, argument: inserted, isExisting: false };
        });
      });
    });

    if (!(result as { isExisting: boolean }).isExisting) {
      this.locks.notifyNewArgument(input.debate_id);
      this.broadcast.newArgument(input.debate_id, result.argument, result.debate);
    }

    return { debate: result.debate, argument: result.argument };
  }

  // DEV-ONLY: client_request_id optional for idempotency
  async submitRuling(input: {
    debate_id: string;
    content: string;
    close?: boolean;
    client_request_id?: string | null;
  }): Promise<{ debate: Debate; argument: Argument }> {
    validateContentSize(input.content);

    const result = await this.locks.withLock(input.debate_id, async () => {
      return await withSqliteBusyRetry(() => {
        return this.db.runImmediateTransaction(() => {
          const debate = this.db.ensureDebateExists(input.debate_id);

          // Idempotency check if client_request_id provided
          if (input.client_request_id) {
            const existing = this.db.findArgumentByClientRequestId(
              input.debate_id,
              input.client_request_id
            );
            if (existing) return { debate, argument: existing, isExisting: true };
          }

          if (!isActionAllowed(debate.state, 'arbitrator', 'submit_ruling')) {
            throw toActionNotAllowedError(debate.state, 'arbitrator', 'submit_ruling');
          }

          const nextSeq = this.db.getNextSeq(input.debate_id);
          const argument: Omit<Argument, 'created_at'> = {
            id: crypto.randomUUID(),
            debate_id: input.debate_id,
            parent_id: null,
            type: 'RULING',
            role: 'arbitrator',
            content: input.content,
            client_request_id: input.client_request_id ?? null,
            seq: nextSeq
          };

          const inserted = this.db.insertArgument(argument);
          const nextState = calculateNextState(debate.state, 'RULING', 'arbitrator', { close: input.close });
          this.db.updateDebateState(input.debate_id, nextState);
          const updatedDebate = this.db.ensureDebateExists(input.debate_id);
          return { debate: updatedDebate, argument: inserted, isExisting: false };
        });
      });
    });

    if (!(result as { isExisting: boolean }).isExisting) {
      this.locks.notifyNewArgument(input.debate_id);
      this.broadcast.newArgument(input.debate_id, result.argument, result.debate);
    }

    return { debate: result.debate, argument: result.argument };
  }
}
