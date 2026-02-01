'use client';

import { use } from 'react';
import { Loader2, WifiOff, Wifi } from 'lucide-react';
import { useDebate } from '@/hooks/use-debate';
import { ArgumentList } from '@/components/debate/argument-list';
import { ActionArea } from '@/components/debate/action-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import type { DebateState } from '@/lib/types';

const stateLabels: Record<DebateState, string> = {
  AWAITING_OPPONENT: 'Waiting for Opponent',
  AWAITING_PROPOSER: 'Waiting for Proposer',
  AWAITING_ARBITRATOR: 'Waiting for Arbitrator',
  INTERVENTION_PENDING: 'Intervention Pending',
  CLOSED: 'Closed',
};

export default function DebatePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const {
    debate,
    arguments: args,
    connected,
    error,
    submitIntervention,
    submitRuling,
  } = useDebate(id);

  if (error && !debate) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-destructive">
        <WifiOff className="h-12 w-12 mb-4" />
        <p className="text-lg">Connection Error</p>
        <p className="text-sm mt-1 text-muted-foreground">{error}</p>
      </div>
    );
  }

  if (!debate) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex h-14 items-center justify-between border-b px-4">
        <div className="flex items-center gap-3 min-w-0">
          <h1 className="font-semibold truncate">{debate.title}</h1>
          <Badge variant="secondary" className="shrink-0">
            {stateLabels[debate.state]}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <div
            className={cn(
              'h-2 w-2 rounded-full',
              connected ? 'bg-green-500' : 'bg-red-500'
            )}
            title={connected ? 'Connected' : 'Disconnected'}
          />
          {connected ? (
            <Wifi className="h-4 w-4 text-green-500" />
          ) : (
            <WifiOff className="h-4 w-4 text-red-500" />
          )}
        </div>
      </div>

      {/* Arguments */}
      <div className="flex-1 overflow-hidden">
        <ArgumentList arguments={args} />
      </div>

      {/* Action Area */}
      <Separator />
      <div className="p-4">
        <ActionArea
          state={debate.state}
          onIntervention={submitIntervention}
          onRuling={submitRuling}
        />
      </div>
    </div>
  );
}
