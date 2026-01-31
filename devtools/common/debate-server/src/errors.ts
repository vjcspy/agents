export class AppError extends Error {
  public readonly code: string;
  public readonly details: Record<string, unknown> | undefined;
  public readonly statusCode: number;

  constructor(
    code: string,
    message: string,
    statusCode: number,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.code = code;
    this.details = details;
    this.statusCode = statusCode;
  }
}

export class NotFoundError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super('NOT_FOUND', message, 404, details);
  }
}

export class DebateNotFoundError extends AppError {
  constructor(debateId: string) {
    super('DEBATE_NOT_FOUND', `Debate not found: ${debateId}`, 404, { debate_id: debateId });
  }
}

export class ArgumentNotFoundError extends AppError {
  constructor(argumentId: string) {
    super('ARGUMENT_NOT_FOUND', `Argument not found: ${argumentId}`, 404, { argument_id: argumentId });
  }
}

export class InvalidInputError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super('INVALID_INPUT', message, 400, details);
  }
}

export class ActionNotAllowedError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super('ACTION_NOT_ALLOWED', message, 403, details);
  }
}

export class ContentTooLargeError extends AppError {
  constructor(maxLength: number) {
    super('CONTENT_TOO_LARGE', `Content exceeds max length (${maxLength})`, 413, {
      max_length: maxLength
    });
  }
}

export class UnauthorizedError extends AppError {
  constructor() {
    super('UNAUTHORIZED', 'Unauthorized', 401);
  }
}

