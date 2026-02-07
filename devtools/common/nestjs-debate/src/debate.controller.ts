import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  Post,
  Query,
} from '@nestjs/common';

import { DebateService } from './debate.service';
import { ArgumentService } from './argument.service';
import { InvalidInputError } from './errors';
import { serializeDebate, serializeArgument } from './serializers';
import type { WaiterRole } from './types';

function ok<T>(data: T) {
  return { success: true as const, data };
}

// Helper to serialize debate+argument response (write operations)
function serializeWriteResult(result: { debate: any; argument: any }) {
  return {
    debate: serializeDebate(result.debate),
    argument: serializeArgument(result.argument),
  };
}

@Controller()
export class DebateController {
  constructor(
    private readonly debateService: DebateService,
    private readonly argumentService: ArgumentService,
  ) {}

  @Get('health')
  healthCheck() {
    return ok({ status: 'ok' });
  }

  // GET /debates?state=...&limit=...&offset=...
  @Get('debates')
  async listDebates(
    @Query('state') state?: string,
    @Query('limit') limitRaw?: string,
    @Query('offset') offsetRaw?: string,
  ) {
    const limit = limitRaw ? parseInt(limitRaw, 10) : undefined;
    const offset = offsetRaw ? parseInt(offsetRaw, 10) : undefined;

    if (limitRaw && (!Number.isFinite(limit) || (limit as number) < 0)) {
      throw new InvalidInputError('Invalid limit parameter');
    }
    if (offsetRaw && (!Number.isFinite(offset) || (offset as number) < 0)) {
      throw new InvalidInputError('Invalid offset parameter');
    }

    const result = await this.debateService.listDebates({ state, limit, offset });
    return ok({
      debates: result.debates.map(serializeDebate),
      total: result.total,
    });
  }

  // POST /debates
  @Post('debates')
  async createDebate(
    @Body()
    body: {
      debate_id: string;
      title: string;
      debate_type: string;
      motion_content: string;
      client_request_id: string;
    },
  ) {
    if (
      !body.debate_id ||
      !body.title ||
      !body.debate_type ||
      !body.motion_content ||
      !body.client_request_id
    ) {
      throw new InvalidInputError('Missing required fields');
    }

    const result = await this.debateService.createDebate({
      debate_id: body.debate_id,
      title: body.title,
      debate_type: body.debate_type,
      motion_content: body.motion_content,
      client_request_id: body.client_request_id,
    });
    return ok(serializeWriteResult(result));
  }

  // GET /debates/:id?limit=N
  @Get('debates/:id')
  async getDebate(
    @Param('id') debateId: string,
    @Query('limit') limitRaw?: string,
  ) {
    let limit: number | undefined;
    if (limitRaw !== undefined) {
      limit = parseInt(limitRaw, 10);
      if (!Number.isFinite(limit)) {
        throw new InvalidInputError('Invalid limit parameter', { limit: limitRaw });
      }
      if (limit < 0) {
        throw new InvalidInputError('limit must be non-negative', { limit });
      }
    }

    const result = await this.debateService.getDebateWithArgs(debateId, limit);
    return ok({
      debate: serializeDebate(result.debate),
      motion: result.motion ? serializeArgument(result.motion) : null,
      arguments: result.arguments.map(serializeArgument),
    });
  }

  // DELETE /debates/:id
  @Delete('debates/:id')
  async deleteDebate(@Param('id') debateId: string) {
    await this.debateService.deleteDebate(debateId);
    return ok({ deleted: true });
  }

  // POST /debates/:id/arguments
  @Post('debates/:id/arguments')
  async submitArgument(
    @Param('id') debateId: string,
    @Body()
    body: {
      role: 'proposer' | 'opponent';
      target_id: string;
      content: string;
      client_request_id: string;
    },
  ) {
    if (!body.role || !body.target_id || !body.content || !body.client_request_id) {
      throw new InvalidInputError('Missing required fields');
    }

    const result = await this.argumentService.submitClaim({
      debate_id: debateId,
      role: body.role,
      target_id: body.target_id,
      content: body.content,
      client_request_id: body.client_request_id,
    });
    return ok(serializeWriteResult(result));
  }

  // POST /debates/:id/appeal
  @Post('debates/:id/appeal')
  async submitAppeal(
    @Param('id') debateId: string,
    @Body()
    body: {
      target_id: string;
      content: string;
      client_request_id: string;
    },
  ) {
    if (!body.target_id || !body.content || !body.client_request_id) {
      throw new InvalidInputError('Missing required fields');
    }

    const result = await this.argumentService.submitAppeal({
      debate_id: debateId,
      target_id: body.target_id,
      content: body.content,
      client_request_id: body.client_request_id,
    });
    return ok(serializeWriteResult(result));
  }

  // POST /debates/:id/resolution
  @Post('debates/:id/resolution')
  async submitResolution(
    @Param('id') debateId: string,
    @Body()
    body: {
      target_id: string;
      content: string;
      client_request_id: string;
    },
  ) {
    if (!body.target_id || !body.content || !body.client_request_id) {
      throw new InvalidInputError('Missing required fields');
    }

    const result = await this.argumentService.submitResolution({
      debate_id: debateId,
      target_id: body.target_id,
      content: body.content,
      client_request_id: body.client_request_id,
    });
    return ok(serializeWriteResult(result));
  }

  // POST /debates/:id/intervention (DEV-ONLY Arbitrator)
  @Post('debates/:id/intervention')
  async submitIntervention(
    @Param('id') debateId: string,
    @Body() body: { content?: string; client_request_id?: string },
  ) {
    const result = await this.argumentService.submitIntervention({
      debate_id: debateId,
      content: body.content,
      client_request_id: body.client_request_id,
    });
    return ok(serializeWriteResult(result));
  }

  // POST /debates/:id/ruling (DEV-ONLY Arbitrator)
  @Post('debates/:id/ruling')
  async submitRuling(
    @Param('id') debateId: string,
    @Body() body: { content: string; close?: boolean; client_request_id?: string },
  ) {
    if (!body.content) {
      throw new InvalidInputError('Missing required fields');
    }

    const result = await this.argumentService.submitRuling({
      debate_id: debateId,
      content: body.content,
      close: body.close,
      client_request_id: body.client_request_id,
    });
    return ok(serializeWriteResult(result));
  }

  // GET /debates/:id/poll?argument_id=...&role=...
  @Get('debates/:id/poll')
  async poll(
    @Param('id') debateId: string,
    @Query('argument_id') argumentId?: string,
    @Query('role') role?: string,
  ) {
    if (!role || (role !== 'proposer' && role !== 'opponent')) {
      throw new InvalidInputError('Invalid role', { role });
    }

    const result = await this.debateService.poll({
      debate_id: debateId,
      argument_id: argumentId || null,
      role: role as WaiterRole,
    });
    return ok(result);
  }
}
