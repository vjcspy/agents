import { Injectable } from '@nestjs/common';
import { randomUUID } from 'crypto';

import { DebatePrismaService } from './debate-prisma.service';
import { LockService } from './lock.service';
import { DebateGateway } from './debate.gateway';
import {
  ActionNotAllowedError,
  ArgumentNotFoundError,
  ContentTooLargeError,
  DebateNotFoundError,
  InvalidInputError,
} from './errors';
import { calculateNextState, isActionAllowed } from './state-machine';
import { serializeDebate, serializeArgument } from './serializers';
import type { ArgumentType, DebateState, Role } from './types';

const MAX_CONTENT_LENGTH = 10 * 1024; // 10KB

function validateContentSize(content: string): void {
  if (content.length > MAX_CONTENT_LENGTH) {
    throw new ContentTooLargeError(MAX_CONTENT_LENGTH);
  }
}

function toActionNotAllowedError(
  state: DebateState,
  role: Role,
  action: string,
): ActionNotAllowedError {
  const allowedRoles: Role[] =
    state === 'AWAITING_OPPONENT'
      ? ['opponent', 'arbitrator']
      : state === 'AWAITING_PROPOSER'
        ? ['proposer', 'arbitrator']
        : state === 'AWAITING_ARBITRATOR' || state === 'INTERVENTION_PENDING'
          ? ['arbitrator']
          : [];

  const suggestion =
    state === 'CLOSED'
      ? 'This debate is closed'
      : `Wait for ${allowedRoles.join(' or ')} to submit`;

  return new ActionNotAllowedError(
    `Role '${role}' cannot perform '${action}' in state '${state}'`,
    { current_state: state, allowed_roles: allowedRoles, suggestion },
  );
}

@Injectable()
export class ArgumentService {
  constructor(
    private readonly prisma: DebatePrismaService,
    private readonly locks: LockService,
    private readonly gateway: DebateGateway,
  ) {}

  /**
   * Core method that handles argument submission with locking, idempotency,
   * state validation, seq assignment, and WebSocket broadcast.
   */
  private async submitArgument(input: {
    debate_id: string;
    role: Role;
    parent_id: string | null;
    type: ArgumentType;
    content: string;
    client_request_id: string | null;
    action_name: string;
    close?: boolean;
  }) {
    validateContentSize(input.content);

    const result = await this.locks.withLock(input.debate_id, async () => {
      return this.prisma.$transaction(async (tx) => {
        // 1. Check debate exists
        const debate = await tx.debate.findUnique({
          where: { id: input.debate_id },
        });
        if (!debate) throw new DebateNotFoundError(input.debate_id);

        // 2. Idempotency check
        if (input.client_request_id) {
          const existing = await tx.argument.findFirst({
            where: {
              debateId: input.debate_id,
              clientRequestId: input.client_request_id,
            },
          });
          if (existing) {
            return { debate, argument: existing, isExisting: true };
          }
        }

        // 3. Validate parent exists and belongs to debate
        if (input.parent_id) {
          const parent = await tx.argument.findUnique({
            where: { id: input.parent_id },
          });
          if (!parent || parent.debateId !== input.debate_id) {
            throw new InvalidInputError(
              'target_id does not belong to this debate',
              { debate_id: input.debate_id, target_id: input.parent_id },
            );
          }
        }

        // 4. Validate state allows this action
        if (
          !isActionAllowed(
            debate.state as DebateState,
            input.role,
            input.action_name as any,
          )
        ) {
          throw toActionNotAllowedError(
            debate.state as DebateState,
            input.role,
            input.action_name,
          );
        }

        // 5. Get next seq (atomic within transaction)
        const maxSeq = await tx.argument.aggregate({
          where: { debateId: input.debate_id },
          _max: { seq: true },
        });
        const nextSeq = (maxSeq._max.seq ?? 0) + 1;

        // 6. Insert argument
        const argument = await tx.argument.create({
          data: {
            id: randomUUID(),
            debateId: input.debate_id,
            parentId: input.parent_id,
            type: input.type,
            role: input.role,
            content: input.content,
            clientRequestId: input.client_request_id,
            seq: nextSeq,
          },
        });

        // 7. Update debate state
        const nextState = calculateNextState(
          debate.state as DebateState,
          input.type,
          input.role,
          { close: input.close },
        );
        const updatedDebate = await tx.debate.update({
          where: { id: input.debate_id },
          data: {
            state: nextState,
            updatedAt: new Date().toISOString().replace('T', ' ').replace(/\.\d+Z$/, ''),
          },
        });

        return { debate: updatedDebate, argument, isExisting: false };
      });
    });

    // 8. Broadcast via WebSocket (after transaction commits)
    if (!result.isExisting) {
      this.gateway.broadcastNewArgument(
        input.debate_id,
        serializeDebate(result.debate as any) as unknown as Record<string, unknown>,
        serializeArgument(result.argument as any) as unknown as Record<string, unknown>,
      );
    }

    return { debate: result.debate, argument: result.argument };
  }

  async submitClaim(input: {
    debate_id: string;
    role: 'proposer' | 'opponent';
    target_id: string;
    content: string;
    client_request_id: string;
  }) {
    return this.submitArgument({
      debate_id: input.debate_id,
      role: input.role,
      parent_id: input.target_id,
      type: 'CLAIM',
      content: input.content,
      client_request_id: input.client_request_id,
      action_name: 'submit_claim',
    });
  }

  async submitAppeal(input: {
    debate_id: string;
    target_id: string;
    content: string;
    client_request_id: string;
  }) {
    return this.submitArgument({
      debate_id: input.debate_id,
      role: 'proposer',
      parent_id: input.target_id,
      type: 'APPEAL',
      content: input.content,
      client_request_id: input.client_request_id,
      action_name: 'submit_appeal',
    });
  }

  async submitResolution(input: {
    debate_id: string;
    target_id: string;
    content: string;
    client_request_id: string;
  }) {
    return this.submitArgument({
      debate_id: input.debate_id,
      role: 'proposer',
      parent_id: input.target_id,
      type: 'RESOLUTION',
      content: input.content,
      client_request_id: input.client_request_id,
      action_name: 'submit_resolution',
    });
  }

  async submitIntervention(input: {
    debate_id: string;
    content?: string | null;
    client_request_id?: string | null;
  }) {
    return this.submitArgument({
      debate_id: input.debate_id,
      role: 'arbitrator',
      parent_id: null,
      type: 'INTERVENTION',
      content: input.content ?? '',
      client_request_id: input.client_request_id ?? null,
      action_name: 'submit_intervention',
    });
  }

  async submitRuling(input: {
    debate_id: string;
    content: string;
    close?: boolean;
    client_request_id?: string | null;
  }) {
    return this.submitArgument({
      debate_id: input.debate_id,
      role: 'arbitrator',
      parent_id: null,
      type: 'RULING',
      content: input.content,
      client_request_id: input.client_request_id ?? null,
      action_name: 'submit_ruling',
      close: input.close,
    });
  }
}
