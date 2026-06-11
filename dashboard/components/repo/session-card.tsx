'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ExternalLink, ChevronDown, Clock, GitPullRequest, AlertCircle, CheckCircle } from 'lucide-react';
import { RemediationSession } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

interface SessionCardProps {
  session: RemediationSession;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'running':
      return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
    case 'needs_review':
      return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Clock className="h-4 w-4 text-gray-500" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'running':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'needs_review':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'failed':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

const getPolicyDecisionColor = (decision: string) => {
  switch (decision) {
    case 'auto_merge':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'human_review':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'blocked':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

export function SessionCard({ session }: SessionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };
  
  return (
    <Card className="mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            {getStatusIcon(session.status)}
            <span className="capitalize">{session.agent_type.replace('_', ' ')}</span>
            <Badge 
              className={`capitalize ${getStatusColor(session.status)}`}
              variant="outline"
            >
              {session.status.replace('_', ' ')}
            </Badge>
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {session.pr_url && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(session.pr_url!, '_blank')}
              >
                <GitPullRequest className="h-3 w-3 mr-1" />
                View PR
                <ExternalLink className="h-3 w-3 ml-1" />
              </Button>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Duration: {formatDuration(session.duration_seconds)}
          </span>
          
          <span>
            Started: {formatDistanceToNow(new Date(session.started_at), { addSuffix: true })}
          </span>
          
          <Badge 
            className={`capitalize ${getPolicyDecisionColor(session.policy_decision)}`}
            variant="outline"
          >
            {session.policy_decision.replace('_', ' ')}
          </Badge>
          
          <span className="font-medium">
            Confidence: {Math.round(session.confidence_score * 100)}%
          </span>
        </div>
      </CardHeader>
      
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CardContent className="pt-0">
          <Button 
            variant="ghost" 
            className="w-full justify-between p-0"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <span>Evidence Bundle</span>
            <ChevronDown className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          </Button>
        </CardContent>
        
        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="bg-muted rounded-md p-4 text-sm">
              <pre className="whitespace-pre-wrap text-xs">
                {JSON.stringify(session.evidence_bundle, null, 2)}
              </pre>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}