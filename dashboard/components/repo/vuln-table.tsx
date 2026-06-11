'use client';

import React, { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, ExternalLink, RotateCcw, EyeOff } from 'lucide-react';
import { Vulnerability } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

interface VulnTableProps {
  vulnerabilities: Vulnerability[];
  repositoryId: string;
  onIgnore: (vulnId: string) => Promise<void>;
  onRetry: (vulnId: string) => Promise<void>;
}

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

const getStatusColor = (status: string) => {
  switch (status) {
    case 'fixed':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'remediating':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'blocked':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    case 'ignored':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    case 'triaging':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

export function VulnTable({ vulnerabilities, repositoryId, onIgnore, onRetry }: VulnTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  
  // Filter vulnerabilities based on search and filters
  const filteredVulns = vulnerabilities.filter((vuln) => {
    const matchesSearch = searchQuery === '' || 
      vuln.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      vuln.package_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (vuln.cve_id && vuln.cve_id.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesSeverity = severityFilter === 'all' || vuln.severity === severityFilter;
    const matchesStatus = statusFilter === 'all' || vuln.status === statusFilter;
    
    return matchesSearch && matchesSeverity && matchesStatus;
  });
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Vulnerabilities</CardTitle>
        
        {/* Filters */}
        <div className="flex gap-4 items-center flex-wrap">
          <div className="flex-1 min-w-64">
            <Input
              placeholder="Search by CVE, package, or title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>
          
          <Select value={severityFilter} onValueChange={(value) => setSeverityFilter(value || 'all')}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Severity</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value || 'all')}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="detected">Detected</SelectItem>
              <SelectItem value="triaging">Triaging</SelectItem>
              <SelectItem value="remediating">Remediating</SelectItem>
              <SelectItem value="fixed">Fixed</SelectItem>
              <SelectItem value="blocked">Blocked</SelectItem>
              <SelectItem value="ignored">Ignored</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>CVE / Title</TableHead>
              <TableHead>Package</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Detected</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredVulns.map((vuln) => (
              <TableRow key={vuln.id}>
                <TableCell>
                  <div>
                    <div className="flex items-center gap-2">
                      {vuln.cve_id ? (
                        <Button
                          variant="link"
                          size="sm"
                          className="p-0 h-auto font-medium text-foreground"
                          onClick={() => window.open(`https://cve.mitre.org/cgi-bin/cvename.cgi?name=${vuln.cve_id}`, '_blank')}
                        >
                          {vuln.cve_id}
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </Button>
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {vuln.title}
                    </p>
                  </div>
                </TableCell>
                
                <TableCell>
                  <div>
                    <span className="font-medium">{vuln.package_name}</span>
                    <p className="text-sm text-muted-foreground">
                      v{vuln.package_version}
                      {vuln.fix_version && (
                        <span className="text-green-600"> → v{vuln.fix_version}</span>
                      )}
                    </p>
                  </div>
                </TableCell>
                
                <TableCell>
                  <Badge variant={getSeverityColor(vuln.severity)} className="capitalize">
                    {vuln.severity}
                  </Badge>
                </TableCell>
                
                <TableCell>
                  <Badge 
                    className={`capitalize ${getStatusColor(vuln.status)}`}
                    variant="outline"
                  >
                    {vuln.status.replace('_', ' ')}
                  </Badge>
                </TableCell>
                
                <TableCell>
                  <span className="text-sm text-muted-foreground">
                    {formatDistanceToNow(new Date(vuln.detected_at), { addSuffix: true })}
                  </span>
                </TableCell>
                
                <TableCell>
                  <div className="flex gap-2">
                    {vuln.status !== 'ignored' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onIgnore(vuln.id)}
                        className="h-8 px-2"
                      >
                        <EyeOff className="h-3 w-3" />
                      </Button>
                    )}
                    
                    {vuln.status === 'blocked' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onRetry(vuln.id)}
                        className="h-8 px-2"
                      >
                        <RotateCcw className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        
        {filteredVulns.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            No vulnerabilities match your filters.
          </div>
        )}
      </CardContent>
    </Card>
  );
}