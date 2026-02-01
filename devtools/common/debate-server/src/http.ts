import express, { type NextFunction, type Request, type Response } from 'express';

import { config } from './config.js';
import { ActionNotAllowedError, AppError, InvalidInputError, UnauthorizedError } from './errors.js';
import type { ErrorResponse, SuccessResponse } from './types.js';
import type { ArgumentService, DebateService } from './services.js';

function requireAuth(req: Request): void {
  if (!config.authToken) return;
  const header = req.header('authorization') || '';
  const [scheme, token] = header.split(' ');
  if (scheme !== 'Bearer' || token !== config.authToken) throw new UnauthorizedError();
}

function ok<T>(data: T): SuccessResponse<T> {
  return { success: true, data };
}

function errorEnvelope(err: unknown): { statusCode: number; body: ErrorResponse } {
  if (err instanceof AppError) {
    // Build flat error object (no nested details)
    const errorObj: Record<string, unknown> = {
      code: err.code,
      message: err.message,
    };

    // Add suggestion if present
    if (err.suggestion) {
      errorObj.suggestion = err.suggestion;
    }

    // Add ActionNotAllowedError specific fields (flat)
    if (err instanceof ActionNotAllowedError) {
      errorObj.current_state = err.currentState;
      errorObj.allowed_roles = err.allowedRoles;
    }

    // Add extra fields (flat)
    if (err.extraFields) {
      Object.assign(errorObj, err.extraFields);
    }

    return {
      statusCode: err.statusCode,
      body: {
        success: false,
        error: errorObj as ErrorResponse['error']
      }
    };
  }

  return {
    statusCode: 500,
    body: { success: false, error: { code: 'INTERNAL_ERROR', message: 'Internal error' } }
  };
}

export function createHttpApp(services: {
  debate: DebateService;
  argument: ArgumentService;
}) {
  const app = express();

  app.use(express.json({ limit: config.maxContentLength + 1024 }));

  app.use((req, _res, next) => {
    try {
      requireAuth(req);
      next();
    } catch (err) {
      next(err);
    }
  });

  app.get('/health', (_req, res) => {
    res.status(200).json(ok({ status: 'ok' }));
  });

  // GET /debates?state=...&limit=...&offset=...
  app.get('/debates', (req, res, next) => {
    try {
      const state = req.query.state as string | undefined;
      const limitRaw = req.query.limit as string | undefined;
      const offsetRaw = req.query.offset as string | undefined;

      const limit = limitRaw ? Number.parseInt(limitRaw, 10) : undefined;
      const offset = offsetRaw ? Number.parseInt(offsetRaw, 10) : undefined;

      if (limitRaw && (!Number.isFinite(limit) || (limit as number) < 0)) {
        throw new InvalidInputError('Invalid limit parameter');
      }
      if (offsetRaw && (!Number.isFinite(offset) || (offset as number) < 0)) {
        throw new InvalidInputError('Invalid offset parameter');
      }

      const result = services.debate.listDebates({ state, limit, offset });
      res.status(200).json(ok(result));
    } catch (err) {
      next(err);
    }
  });

  app.post('/debates', async (req, res, next) => {
    try {
      const body = req.body as Partial<{
        debate_id: string;
        title: string;
        debate_type: string;
        motion_content: string;
        client_request_id: string;
      }>;
      if (!body.debate_id || !body.title || !body.debate_type || !body.motion_content || !body.client_request_id) {
        throw new InvalidInputError('Missing required fields');
      }
      const created = await services.debate.createDebate({
        debate_id: body.debate_id,
        title: body.title,
        debate_type: body.debate_type,
        motion_content: body.motion_content,
        client_request_id: body.client_request_id
      });
      res.status(201).json(ok(created));
    } catch (err) {
      next(err);
    }
  });

  // GET /debates/:id?limit=N
  // motion ALWAYS included (not counted in limit)
  // limit=N returns N most recent arguments (excluding motion)
  // limit=0 returns arguments=[]
  // limit not set returns all arguments
  // limit negative or invalid → INVALID_INPUT
  app.get('/debates/:id', (req, res, next) => {
    try {
      const debateId = req.params.id;
      const limitRaw = req.query.limit as string | undefined;

      let limit: number | undefined;
      if (limitRaw !== undefined) {
        limit = Number.parseInt(limitRaw, 10);
        if (!Number.isFinite(limit)) {
          throw new InvalidInputError('Invalid limit parameter', { limit: limitRaw });
        }
        if (limit < 0) {
          throw new InvalidInputError('limit must be non-negative', { limit });
        }
      }

      const result = services.debate.getDebateWithArgs(debateId, limit);
      res.status(200).json(ok(result));
    } catch (err) {
      next(err);
    }
  });

  app.post('/debates/:id/arguments', async (req, res, next) => {
    try {
      const debateId = req.params.id;
      const body = req.body as Partial<{
        role: 'proposer' | 'opponent';
        target_id: string;
        content: string;
        client_request_id: string;
      }>;
      if (!body.role || !body.target_id || !body.content || !body.client_request_id) {
        throw new InvalidInputError('Missing required fields');
      }
      const created = await services.argument.submitClaim({
        debate_id: debateId,
        role: body.role,
        target_id: body.target_id,
        content: body.content,
        client_request_id: body.client_request_id
      });
      res.status(201).json(ok(created));
    } catch (err) {
      next(err);
    }
  });

  app.post('/debates/:id/appeal', async (req, res, next) => {
    try {
      const debateId = req.params.id;
      const body = req.body as Partial<{
        target_id: string;
        content: string;
        client_request_id: string;
      }>;
      if (!body.target_id || !body.content || !body.client_request_id) {
        throw new InvalidInputError('Missing required fields');
      }
      const created = await services.argument.submitAppeal({
        debate_id: debateId,
        target_id: body.target_id,
        content: body.content,
        client_request_id: body.client_request_id
      });
      res.status(201).json(ok(created));
    } catch (err) {
      next(err);
    }
  });

  app.post('/debates/:id/resolution', async (req, res, next) => {
    try {
      const debateId = req.params.id;
      const body = req.body as Partial<{
        target_id: string;
        content: string;
        client_request_id: string;
      }>;
      if (!body.target_id || !body.content || !body.client_request_id) {
        throw new InvalidInputError('Missing required fields');
      }
      const created = await services.argument.submitResolution({
        debate_id: debateId,
        target_id: body.target_id,
        content: body.content,
        client_request_id: body.client_request_id
      });
      res.status(201).json(ok(created));
    } catch (err) {
      next(err);
    }
  });

  // DEV-ONLY: Arbitrator intervention
  app.post('/debates/:id/intervention', async (req, res, next) => {
    try {
      const debateId = req.params.id;
      const body = req.body as Partial<{ content: string; client_request_id: string }>;
      const created = await services.argument.submitIntervention({
        debate_id: debateId,
        content: body.content,
        client_request_id: body.client_request_id
      });
      res.status(201).json(ok(created));
    } catch (err) {
      next(err);
    }
  });

  // DEV-ONLY: Arbitrator ruling
  app.post('/debates/:id/ruling', async (req, res, next) => {
    try {
      const debateId = req.params.id;
      const body = req.body as Partial<{ content: string; close?: boolean; client_request_id: string }>;
      if (!body.content) throw new InvalidInputError('Missing required fields');
      const created = await services.argument.submitRuling({
        debate_id: debateId,
        content: body.content,
        close: body.close,
        client_request_id: body.client_request_id
      });
      res.status(201).json(ok(created));
    } catch (err) {
      next(err);
    }
  });

  app.get('/debates/:id/wait', async (req, res, next) => {
    try {
      const debateId = req.params.id;
      const argumentId = (req.query.argument_id as string | undefined) ?? undefined;
      const role = req.query.role as 'proposer' | 'opponent' | undefined;
      if (!role || (role !== 'proposer' && role !== 'opponent')) {
        throw new InvalidInputError('Invalid role', { role });
      }
      const result = await services.debate.waitForResponse({
        debate_id: debateId,
        argument_id: argumentId,
        role,
        poll_timeout_ms: config.pollTimeoutMs
      });
      res.status(200).json(ok(result));
    } catch (err) {
      next(err);
    }
  });

  app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
    const { statusCode, body } = errorEnvelope(err);
    res.status(statusCode).json(body);
  });

  return app;
}
