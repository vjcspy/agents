export { debateMachine } from './machine';
export {
  canTransition,
  transition,
  getAvailableActions,
  toDebateEvent,
} from './utils';
export type {
  DebateState,
  ArgumentType,
  Role,
  DebateEvent,
} from './types';
