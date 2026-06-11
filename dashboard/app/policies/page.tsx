'use client';

import React, { useState } from 'react';
import { MainLayout } from '@/components/layout/main-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Shield, CheckCircle, AlertCircle, XCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface PolicyDecision {
  id: string;
  repository: string;
  vulnerability: string;
  decision: 'auto_merge' | 'human_review' | 'blocked';
  reason: string;
  confidence: number;
  timestamp: string;
}

const mockPolicyDecisions: PolicyDecision[] = [
  {
    id: '1',
    repository: 'gaurav21/superset',
    vulnerability: 'PyJWT upgrade to 2.8.0',
    decision: 'auto_merge',
    reason: 'High confidence, patch upgrade, tests pass',
    confidence: 0.92,
    timestamp: '2024-06-09T10:15:00Z'
  },
  {
    id: '2',
    repository: 'gaurav21/superset',
    vulnerability: 'Flask upgrade to 3.0.0',
    decision: 'human_review',
    reason: 'Major version upgrade, potential breaking changes',
    confidence: 0.65,
    timestamp: '2024-06-08T14:30:00Z'
  },
  {
    id: '3',
    repository: 'org/api-gateway',
    vulnerability: 'Express.js security patch',
    decision: 'blocked',
    reason: 'Touches sensitive authentication code',
    confidence: 0.45,
    timestamp: '2024-06-08T09:20:00Z'
  }
];

const getDecisionIcon = (decision: string) => {
  switch (decision) {
    case 'auto_merge':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'human_review':
      return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    case 'blocked':
      return <XCircle className="h-4 w-4 text-red-500" />;
    default:
      return null;
  }
};

const getDecisionColor = (decision: string) => {
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

export default function PoliciesPage() {
  // Policy configuration state
  const [autoMergeConfidence, setAutoMergeConfidence] = useState([80]);
  const [maxFilesTouched, setMaxFilesTouched] = useState([10]);
  const [patchAutoMerge, setPatchAutoMerge] = useState(true);
  const [minorAutoMerge, setMinorAutoMerge] = useState(true);
  const [majorAutoMerge, setMajorAutoMerge] = useState(false);
  const [sensitivePaths, setSensitivePaths] = useState('auth/, crypto/, security/');
  const [selectedRepo, setSelectedRepo] = useState('all');
  
  const handleSavePolicies = () => {
    console.log('Saving policies...', {
      autoMergeConfidence: autoMergeConfidence[0],
      maxFilesTouched: maxFilesTouched[0],
      patchAutoMerge,
      minorAutoMerge,
      majorAutoMerge,
      sensitivePaths,
      selectedRepo
    });
  };
  
  return (
    <MainLayout title="Security Policies">
      <div className="space-y-6">
        <div>
          <p className="text-muted-foreground">
            Configure automated remediation policies and trust boundaries for your repositories.
          </p>
        </div>
        
        {/* Trust Boundary Visualization */}
        <Card>
          <CardHeader>
            <CardTitle>Trust Boundary Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {/* Auto-merge Zone */}
              <div className="p-4 border border-green-200 rounded-lg bg-green-50 dark:bg-green-950 dark:border-green-800">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <h3 className="font-semibold text-green-800 dark:text-green-200">Auto-merge Zone</h3>
                </div>
                <ul className="text-sm text-green-700 dark:text-green-300 space-y-1">
                  <li>• Confidence ≥ {autoMergeConfidence[0]}%</li>
                  <li>• Files changed ≤ {maxFilesTouched[0]}</li>
                  <li>• No sensitive paths</li>
                  <li>• Tests pass</li>
                </ul>
              </div>
              
              {/* Human Review Zone */}
              <div className="p-4 border border-yellow-200 rounded-lg bg-yellow-50 dark:bg-yellow-950 dark:border-yellow-800">
                <div className="flex items-center gap-2 mb-3">
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                  <h3 className="font-semibold text-yellow-800 dark:text-yellow-200">Human Review</h3>
                </div>
                <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                  <li>• Medium confidence</li>
                  <li>• Major version upgrades</li>
                  <li>• Multiple files changed</li>
                  <li>• Some test failures</li>
                </ul>
              </div>
              
              {/* Blocked Zone */}
              <div className="p-4 border border-red-200 rounded-lg bg-red-50 dark:bg-red-950 dark:border-red-800">
                <div className="flex items-center gap-2 mb-3">
                  <XCircle className="h-5 w-5 text-red-600" />
                  <h3 className="font-semibold text-red-800 dark:text-red-200">Blocked</h3>
                </div>
                <ul className="text-sm text-red-700 dark:text-red-300 space-y-1">
                  <li>• Low confidence</li>
                  <li>• Sensitive paths touched</li>
                  <li>• Test failures</li>
                  <li>• Breaking changes</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Policy Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Policy Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Repository Selection */}
            <div className="space-y-2">
              <Label>Apply to Repository</Label>
              <Select value={selectedRepo} onValueChange={(value) => setSelectedRepo(value || 'all')}>
                <SelectTrigger className="w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Repositories (Global)</SelectItem>
                  <SelectItem value="gaurav21/superset">gaurav21/superset</SelectItem>
                  <SelectItem value="gaurav21/shieldops">gaurav21/shieldops</SelectItem>
                  <SelectItem value="org/api-gateway">org/api-gateway</SelectItem>
                  <SelectItem value="org/auth-service">org/auth-service</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Confidence Threshold */}
            <div className="space-y-3">
              <Label>Auto-merge Confidence Threshold: {autoMergeConfidence[0]}%</Label>
              <Slider
                value={autoMergeConfidence}
                onValueChange={(value) => setAutoMergeConfidence(Array.isArray(value) ? value : [value])}
                max={100}
                min={50}
                step={5}
                className="w-full"
              />
              <p className="text-sm text-muted-foreground">
                Minimum confidence score required for automatic merging
              </p>
            </div>
            
            {/* Max Files Threshold */}
            <div className="space-y-3">
              <Label>Maximum Files Changed: {maxFilesTouched[0]} files</Label>
              <Slider
                value={maxFilesTouched}
                onValueChange={(value) => setMaxFilesTouched(Array.isArray(value) ? value : [value])}
                max={50}
                min={1}
                step={1}
                className="w-full"
              />
              <p className="text-sm text-muted-foreground">
                Maximum number of files that can be changed for auto-merge
              </p>
            </div>
            
            {/* Upgrade Type Rules */}
            <div className="space-y-4">
              <Label className="text-base font-medium">Upgrade Type Rules</Label>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Patch Upgrades (1.0.1 → 1.0.2)</Label>
                    <p className="text-sm text-muted-foreground">Bug fixes and security patches</p>
                  </div>
                  <Switch checked={patchAutoMerge} onCheckedChange={setPatchAutoMerge} />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Minor Upgrades (1.0.0 → 1.1.0)</Label>
                    <p className="text-sm text-muted-foreground">New features, backward compatible</p>
                  </div>
                  <Switch checked={minorAutoMerge} onCheckedChange={setMinorAutoMerge} />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Major Upgrades (1.0.0 → 2.0.0)</Label>
                    <p className="text-sm text-muted-foreground">Breaking changes, requires review</p>
                  </div>
                  <Switch checked={majorAutoMerge} onCheckedChange={setMajorAutoMerge} />
                </div>
              </div>
            </div>
            
            {/* Sensitive Paths */}
            <div className="space-y-3">
              <Label>Sensitive Paths (comma-separated)</Label>
              <Input
                value={sensitivePaths}
                onChange={(e) => setSensitivePaths(e.target.value)}
                placeholder="auth/, crypto/, security/"
              />
              <p className="text-sm text-muted-foreground">
                Files in these paths always require human review
              </p>
            </div>
            
            <div className="flex justify-end">
              <Button onClick={handleSavePolicies}>
                Save Policy Configuration
              </Button>
            </div>
          </CardContent>
        </Card>
        
        {/* Policy Decision Log */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Policy Decisions</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Repository</TableHead>
                  <TableHead>Vulnerability</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Timestamp</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockPolicyDecisions.map((decision) => (
                  <TableRow key={decision.id}>
                    <TableCell>
                      <Badge variant="secondary">{decision.repository}</Badge>
                    </TableCell>
                    <TableCell>
                      <span className="font-medium">{decision.vulnerability}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getDecisionIcon(decision.decision)}
                        <Badge 
                          className={`capitalize ${getDecisionColor(decision.decision)}`}
                          variant="outline"
                        >
                          {decision.decision.replace('_', ' ')}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">{decision.reason}</span>
                    </TableCell>
                    <TableCell>
                      <span className="font-medium">{Math.round(decision.confidence * 100)}%</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {formatDistanceToNow(new Date(decision.timestamp), { addSuffix: true })}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}