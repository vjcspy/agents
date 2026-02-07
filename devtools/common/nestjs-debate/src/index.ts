export { DebateModule } from './debate.module';
export { DebateService } from './debate.service';
export { ArgumentService } from './argument.service';
export { DebateGateway } from './debate.gateway';

// All DTOs (entity, request, response, error) — consumed by @aweave/server for Swagger setup
export * from './dto';

// WS event types — consumed by debate-web for WebSocket typing
export type {
  WsEvent,
  ServerToClientEvent, InitialStateEvent, NewArgumentEvent,
  ClientToServerEvent, SubmitInterventionEvent, SubmitRulingEvent,
} from './ws-types';
