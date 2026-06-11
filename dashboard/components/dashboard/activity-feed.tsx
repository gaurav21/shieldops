'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ActivityEvent } from '@/lib/api';

interface ActivityFeedProps {
  events: ActivityEvent[];
}

const getStatusColor = (color: string) => {
  switch (color) {
    case 'green':
      return 'bg-green-500';
    case 'yellow':
      return 'bg-yellow-500';
    case 'blue':
      return 'bg-blue-500';
    case 'red':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
};

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function ActivityFeed({ events }: ActivityFeedProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {events.map((event) => (
            <div key={event.id} className="flex items-start gap-3">
              <div className={`flex h-8 w-8 items-center justify-center rounded-full ${getStatusColor(event.color)} shrink-0`}>
                <span className="text-sm text-white">{event.icon}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-foreground">{event.message}</p>
                <div className="flex items-center gap-2 mt-1">
                  {event.repository && (
                    <Badge variant="secondary" className="text-xs">
                      {event.repository}
                    </Badge>
                  )}
                  <span className="text-xs text-muted-foreground">
                    {timeAgo(event.timestamp)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
