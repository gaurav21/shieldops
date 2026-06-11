'use client';

import React, { useState } from 'react';
import useSWR from 'swr';
import { MainLayout } from '@/components/layout/main-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Download, ChevronDown, Scan, Settings, Shield, User, FileText } from 'lucide-react';
import { fetcher, AuditEvent } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

const getEventIcon = (eventType: string) => {
  switch (eventType) {
    case 'scan':
      return <Scan className="h-4 w-4 text-blue-500" />;
    case 'session':
      return <Shield className="h-4 w-4 text-green-500" />;
    case 'policy':
      return <Settings className="h-4 w-4 text-yellow-500" />;
    case 'config_change':
      return <Settings className="h-4 w-4 text-orange-500" />;
    case 'auth':
      return <User className="h-4 w-4 text-purple-500" />;
    default:
      return <FileText className="h-4 w-4 text-gray-500" />;
  }
};

const getEventTypeColor = (eventType: string) => {
  switch (eventType) {
    case 'scan':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'session':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'policy':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'config_change':
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    case 'auth':
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

export default function AuditPage() {
  const { data: auditEvents } = useSWR<AuditEvent[]>('/api/audit', fetcher);
  
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('all');
  const [actorFilter, setActorFilter] = useState<string>('');
  const [repoFilter, setRepoFilter] = useState<string>('all');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  
  if (!auditEvents) {
    return (
      <MainLayout title="Audit Trail">
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <FileText className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">Loading audit events...</p>
          </div>
        </div>
      </MainLayout>
    );
  }
  
  // Filter events
  const filteredEvents = auditEvents.filter((event) => {
    const matchesEventType = eventTypeFilter === 'all' || event.event_type === eventTypeFilter;
    const matchesActor = actorFilter === '' || event.actor.toLowerCase().includes(actorFilter.toLowerCase());
    const matchesRepo = repoFilter === 'all' || event.repository === repoFilter;
    
    return matchesEventType && matchesActor && matchesRepo;
  });
  
  const toggleRowExpansion = (eventId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedRows(newExpanded);
  };
  
  const handleExportCSV = () => {
    const csvData = filteredEvents.map(event => ({
      timestamp: event.timestamp,
      event_type: event.event_type,
      actor: event.actor,
      repository: event.repository || 'N/A',
      details: JSON.stringify(event.details)
    }));
    
    const csvContent = "data:text/csv;charset=utf-8," + 
      Object.keys(csvData[0]).join(',') + '\n' +
      csvData.map(row => Object.values(row).map(val => `"${val}"`).join(',')).join('\n');
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `audit-trail-${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  // Get unique repositories for filter
  const repositories = Array.from(new Set(auditEvents.map(e => e.repository).filter(Boolean)));
  
  return (
    <MainLayout title="Audit Trail">
      <div className="space-y-6">
        <div>
          <p className="text-muted-foreground">
            Complete audit log of all security-related events in your organization.
          </p>
        </div>
        
        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Filters
              <Button onClick={handleExportCSV} variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 items-end flex-wrap">
              <div className="space-y-2">
                <label className="text-sm font-medium">Event Type</label>
                <Select value={eventTypeFilter} onValueChange={(value) => setEventTypeFilter(value || 'all')}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="scan">Scans</SelectItem>
                    <SelectItem value="session">Sessions</SelectItem>
                    <SelectItem value="policy">Policy</SelectItem>
                    <SelectItem value="config_change">Config Changes</SelectItem>
                    <SelectItem value="auth">Authentication</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Repository</label>
                <Select value={repoFilter} onValueChange={(value) => setRepoFilter(value || 'all')}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Repositories</SelectItem>
                    {repositories.map((repo) => (
                      <SelectItem key={repo} value={repo!}>{repo}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">Actor</label>
                <Input
                  placeholder="Filter by user..."
                  value={actorFilter}
                  onChange={(e) => setActorFilter(e.target.value)}
                  className="w-48"
                />
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Events Table */}
        <Card>
          <CardHeader>
            <CardTitle>
              Audit Events ({filteredEvents.length} of {auditEvents.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Event</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Repository</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEvents.map((event) => (
                  <React.Fragment key={event.id}>
                    <TableRow className="hover:bg-muted/50">
                      <TableCell>
                        <span className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                        </span>
                        <p className="text-xs text-muted-foreground">
                          {new Date(event.timestamp).toLocaleDateString()} {new Date(event.timestamp).toLocaleTimeString()}
                        </p>
                      </TableCell>
                      
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getEventIcon(event.event_type)}
                          <Badge 
                            className={`capitalize ${getEventTypeColor(event.event_type)}`}
                            variant="outline"
                          >
                            {event.event_type.replace('_', ' ')}
                          </Badge>
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <span className="font-medium">{event.actor}</span>
                      </TableCell>
                      
                      <TableCell>
                        {event.repository ? (
                          <Badge variant="secondary">{event.repository}</Badge>
                        ) : (
                          <span className="text-sm text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        <span className="text-sm text-muted-foreground truncate max-w-xs block">
                          {Object.keys(event.details).length > 0 ? (
                            `${Object.keys(event.details).length} properties`
                          ) : (
                            'No details'
                          )}
                        </span>
                      </TableCell>
                      
                      <TableCell>
                        {Object.keys(event.details).length > 0 && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleRowExpansion(event.id)}
                          >
                            <ChevronDown className={`h-4 w-4 transition-transform ${
                              expandedRows.has(event.id) ? 'rotate-180' : ''
                            }`} />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                    
                    {expandedRows.has(event.id) && Object.keys(event.details).length > 0 && (
                      <TableRow>
                        <TableCell colSpan={6}>
                          <div className="bg-muted/50 rounded-md p-4">
                            <h4 className="font-medium mb-2">Event Details</h4>
                            <pre className="text-xs text-muted-foreground whitespace-pre-wrap overflow-auto">
                              {JSON.stringify(event.details, null, 2)}
                            </pre>
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
            
            {filteredEvents.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No audit events match your filters.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}