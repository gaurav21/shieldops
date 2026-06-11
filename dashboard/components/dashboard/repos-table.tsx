'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ExternalLink, Shield } from 'lucide-react';
import { Repository } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';
import { useRouter } from 'next/navigation';

interface ReposTableProps {
  repositories: Repository[];
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'healthy':
      return <Shield className="h-4 w-4 text-green-500" />;
    case 'needs_attention':
      return <Shield className="h-4 w-4 text-yellow-500" />;
    case 'critical':
      return <Shield className="h-4 w-4 text-red-500" />;
    default:
      return <Shield className="h-4 w-4 text-gray-500" />;
  }
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'destructive';
    case 'high':
      return 'destructive';
    case 'medium':
      return 'secondary';
    case 'low':
      return 'outline';
    default:
      return 'outline';
  }
};

export function ReposTable({ repositories }: ReposTableProps) {
  const router = useRouter();
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Repositories</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Repository</TableHead>
              <TableHead>Vulnerabilities</TableHead>
              <TableHead>Last Scan</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Fix Rate</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {repositories.map((repo) => (
              <TableRow 
                key={repo.id} 
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => router.push(`/repos/${repo.id}`)}
              >
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{repo.full_name}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open('https://github.com/' + repo.full_name, '_blank');
                      }}
                    >
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    {repo.vuln_summary.by_severity.critical > 0 && (
                      <Badge variant={getSeverityColor('critical')} className="text-xs">
                        {repo.vuln_summary.by_severity.critical}C
                      </Badge>
                    )}
                    {repo.vuln_summary.by_severity.high > 0 && (
                      <Badge variant={getSeverityColor('high')} className="text-xs">
                        {repo.vuln_summary.by_severity.high}H
                      </Badge>
                    )}
                    {repo.vuln_summary.by_severity.medium > 0 && (
                      <Badge variant={getSeverityColor('medium')} className="text-xs">
                        {repo.vuln_summary.by_severity.medium}M
                      </Badge>
                    )}
                    {repo.vuln_summary.by_severity.low > 0 && (
                      <Badge variant={getSeverityColor('low')} className="text-xs">
                        {repo.vuln_summary.by_severity.low}L
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  {repo.last_scan_at ? (
                    <span className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(repo.last_scan_at), { addSuffix: true })}
                    </span>
                  ) : (
                    <span className="text-sm text-muted-foreground">Never</span>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {getStatusIcon('healthy')}
                    <span className="capitalize text-sm">{'healthy'.replace('_', ' ')}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-sm font-medium">
                    {'—'}%
                  </span>
                </TableCell>
                <TableCell>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      // Trigger scan - would call API
                      console.log('Running scan for', repo.full_name);
                    }}
                  >
                    Run Scan
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}