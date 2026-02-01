'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import type { Argument, ArgumentType, Role } from '@/lib/types';

const roleColors: Record<Role, string> = {
  proposer: 'bg-blue-500/20 text-blue-700 dark:text-blue-300 border-blue-500/30',
  opponent: 'bg-orange-500/20 text-orange-700 dark:text-orange-300 border-orange-500/30',
  arbitrator: 'bg-purple-500/20 text-purple-700 dark:text-purple-300 border-purple-500/30',
};

const roleLabels: Record<Role, string> = {
  proposer: 'Proposer',
  opponent: 'Opponent',
  arbitrator: 'Arbitrator',
};

const typeColors: Record<ArgumentType, string> = {
  MOTION: 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300',
  CLAIM: 'bg-sky-500/20 text-sky-700 dark:text-sky-300',
  APPEAL: 'bg-amber-500/20 text-amber-700 dark:text-amber-300',
  RULING: 'bg-purple-500/20 text-purple-700 dark:text-purple-300',
  INTERVENTION: 'bg-red-500/20 text-red-700 dark:text-red-300',
  RESOLUTION: 'bg-green-500/20 text-green-700 dark:text-green-300',
};

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
}

type ArgumentCardProps = {
  argument: Argument;
};

export function ArgumentCard({ argument }: ArgumentCardProps) {
  const isArbitrator = argument.role === 'arbitrator';

  return (
    <Card
      className={cn(
        'transition-colors',
        isArbitrator && 'border-purple-500/30 bg-purple-500/5'
      )}
    >
      <CardHeader className="pb-2 pt-3 px-4">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={cn('text-xs', roleColors[argument.role])}>
              {roleLabels[argument.role]}
            </Badge>
            <Badge variant="secondary" className={cn('text-xs', typeColors[argument.type])}>
              {argument.type}
            </Badge>
          </div>
          <span className="text-xs text-muted-foreground">
            {formatRelativeTime(argument.created_at)}
          </span>
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:mt-4 prose-headings:mb-2 prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0 prose-pre:bg-muted prose-pre:text-foreground prose-code:text-foreground prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {argument.content}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
}
