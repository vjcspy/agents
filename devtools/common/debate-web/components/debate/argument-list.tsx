'use client';

import { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ArgumentCard } from './argument-card';
import type { Argument } from '@/lib/types';

type ArgumentListProps = {
  arguments: Argument[];
};

export function ArgumentList({ arguments: args }: ArgumentListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new arguments are added
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [args.length]);

  if (args.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        No arguments yet
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-4 p-4">
        {args.map((arg) => (
          <ArgumentCard key={arg.id} argument={arg} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
