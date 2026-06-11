'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import useSWR, { mutate } from 'swr';
import { MainLayout } from '@/components/layout/main-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { fetcher } from '@/lib/api';
import { Shield, ExternalLink, GitBranch, Play, Loader2, Zap, RefreshCw } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getToken() {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem('shieldops_token') || '';
}

async function apiPost(path: string) {
  const resp = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
  });
  return resp.json();
}

export default function RepositoryDetailPage() {
  const params = useParams();
  const repoId = params.id as string;
  const { data: repo, isLoading } = useSWR<any>(`/api/repos/${repoId}`, fetcher);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [remediating, setRemediating] = useState<string | null>(null);
  const [launchedSessions, setLaunchedSessions] = useState<Record<string, any>>({});

  const handleScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const result = await apiPost(`/api/repos/${repoId}/scan/full`);
      setScanResult(result);
      mutate(`/api/repos/${repoId}`);
      mutate('/api/dashboard/overview');
    } catch (e: any) {
      setScanResult({ error: e.message });
    } finally {
      setScanning(false);
    }
  };

  const handleRemediate = async (vulnId: string) => {
    setRemediating(vulnId);
    try {
      const result = await apiPost(`/api/vulns/${vulnId}/remediate`);
      setLaunchedSessions(prev => ({ ...prev, [vulnId]: result }));
      mutate(`/api/repos/${repoId}`);
    } catch (e: any) {
      setLaunchedSessions(prev => ({ ...prev, [vulnId]: { error: e.detail || e.message } }));
    } finally {
      setRemediating(null);
    }
  };

  if (isLoading || !repo) {
    return (
      <MainLayout title="Repository">
        <div className="flex items-center justify-center h-64">
          <Shield className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </MainLayout>
    );
  }

  const sev = repo.vuln_summary?.by_severity || { critical: 0, high: 0, medium: 0, low: 0 };
  const totalVulns = sev.critical + sev.high + sev.medium + sev.low;

  return (
    <MainLayout title={repo.full_name}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`h-4 w-4 rounded-full ${totalVulns === 0 ? 'bg-green-500' : sev.critical > 0 ? 'bg-red-500' : 'bg-amber-500'}`} />
            <div>
              <h2 className="text-2xl font-bold">{repo.full_name}</h2>
              <p className="text-sm text-muted-foreground">
                {repo.default_branch} · {repo.scan_config?.schedule || 'daily'} scans ·
                {repo.last_scan_at ? ` Last scan: ${new Date(repo.last_scan_at).toLocaleString()}` : ' Never scanned'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleScan}
              disabled={scanning}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              {scanning ? 'Scanning...' : 'Run Scan'}
            </button>
            <a
              href={`https://github.com/${repo.full_name}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <ExternalLink className="h-4 w-4" /> GitHub
            </a>
          </div>
        </div>

        {/* Scan Result */}
        {scanResult && (
          <Card className={scanResult.error ? 'border-red-500/50' : 'border-green-500/50'}>
            <CardContent className="py-3">
              {scanResult.error ? (
                <p className="text-sm text-red-400">Scan failed: {scanResult.error}</p>
              ) : (
                <p className="text-sm text-green-400">
                  ✅ Scan complete — {scanResult.total_vulns_found} vulnerabilities found ({scanResult.new_vulns} new) across {scanResult.packages_scanned} packages
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Severity Overview */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: 'Critical', count: sev.critical, color: 'text-red-500 border-red-500/30' },
            { label: 'High', count: sev.high, color: 'text-amber-500 border-amber-500/30' },
            { label: 'Medium', count: sev.medium, color: 'text-blue-500 border-blue-500/30' },
            { label: 'Low', count: sev.low, color: 'text-green-500 border-green-500/30' },
          ].map(s => (
            <Card key={s.label} className={`border ${s.color.split(' ')[1]}`}>
              <CardContent className="py-4 text-center">
                <p className={`text-3xl font-bold ${s.color.split(' ')[0]}`}>{s.count}</p>
                <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Vulnerabilities */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Vulnerabilities</CardTitle>
            {totalVulns > 0 && (
              <Badge variant="secondary">{totalVulns} total</Badge>
            )}
          </CardHeader>
          <CardContent>
            {(!repo.vulnerabilities || repo.vulnerabilities.length === 0) ? (
              <div className="text-center py-8">
                <Shield className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">No vulnerabilities found</p>
                <p className="text-xs text-muted-foreground mt-1">Click "Run Scan" to check for vulnerabilities</p>
              </div>
            ) : (
              <div className="space-y-3">
                {repo.vulnerabilities.map((v: any) => {
                  const session = launchedSessions[v.id];
                  const isRemediating = remediating === v.id;
                  const sevColors: Record<string, string> = {
                    critical: 'bg-red-500/20 text-red-400',
                    high: 'bg-amber-500/20 text-amber-400',
                    medium: 'bg-blue-500/20 text-blue-400',
                    low: 'bg-green-500/20 text-green-400',
                  };
                  const statusColors: Record<string, string> = {
                    detected: 'bg-gray-500/20 text-gray-400',
                    remediating: 'bg-purple-500/20 text-purple-400',
                    fixed: 'bg-green-500/20 text-green-400',
                    blocked: 'bg-red-500/20 text-red-400',
                  };

                  return (
                    <div key={v.id} className="rounded-lg border p-4 space-y-2">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge className={sevColors[v.severity] || sevColors.medium}>
                              {v.severity}
                            </Badge>
                            <Badge className={statusColors[v.status] || statusColors.detected}>
                              {v.status}
                            </Badge>
                            {v.cve_id && <span className="text-xs text-muted-foreground font-mono">{v.cve_id}</span>}
                          </div>
                          <p className="text-sm font-medium">{v.title}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {v.package_name} {v.current_version}
                            {v.fixed_version && <span className="text-green-400"> → {v.fixed_version}</span>}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {v.status === 'detected' && !session && (
                            <button
                              onClick={() => handleRemediate(v.id)}
                              disabled={isRemediating}
                              className="inline-flex items-center gap-1.5 rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700 disabled:opacity-50"
                            >
                              {isRemediating ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <Zap className="h-3 w-3" />
                              )}
                              Remediate with Devin
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Devin Session Status */}
                      {session && !session.error && (
                        <div className="rounded-md bg-purple-500/10 border border-purple-500/20 p-3">
                          <div className="flex items-center gap-2">
                            <Zap className="h-4 w-4 text-purple-400" />
                            <span className="text-sm font-medium text-purple-300">Devin Session Launched</span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">Session: {session.session_id}</p>
                          <a
                            href={session.session_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 mt-1"
                          >
                            <ExternalLink className="h-3 w-3" /> Open in Devin
                          </a>
                        </div>
                      )}
                      {session?.error && (
                        <p className="text-xs text-red-400">Error: {session.error}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Scan Config */}
        <Card>
          <CardHeader><CardTitle className="text-lg">Scan Configuration</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Schedule</p>
                <p className="font-medium capitalize">{repo.scan_config?.schedule || 'daily'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Auto Fix</p>
                <p className="font-medium">{repo.scan_config?.auto_fix ? '✅ Enabled' : '❌ Disabled'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Threshold</p>
                <p className="font-medium capitalize">{repo.scan_config?.severity_threshold || 'medium'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Scanners</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {(repo.scan_config?.scan_types || []).map((t: string) => (
                    <Badge key={t} variant="secondary" className="text-xs">{t}</Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Remediation Sessions */}
        {repo.recent_sessions && repo.recent_sessions.length > 0 && (
          <Card>
            <CardHeader><CardTitle className="text-lg">Remediation Sessions</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {repo.recent_sessions.map((s: any) => (
                  <div key={s.id} className="flex items-center justify-between rounded-lg border p-3">
                    <div className="flex items-center gap-3">
                      <div className={`h-2.5 w-2.5 rounded-full ${
                        s.status === 'completed' ? 'bg-green-500' : 
                        s.status === 'failed' ? 'bg-red-500' : 
                        s.status === 'running' ? 'bg-purple-500 animate-pulse' : 'bg-amber-500'
                      }`} />
                      <div>
                        <p className="text-sm font-medium">{s.agent_type} · {s.status}</p>
                        <p className="text-xs text-muted-foreground">
                          {s.policy_decision || 'pending'}
                          {s.duration_seconds ? ` · ${Math.round(s.duration_seconds / 60)}m` : ''}
                          {s.acu_cost ? ` · ${s.acu_cost.toFixed(1)} ACU` : ''}
                        </p>
                      </div>
                    </div>
                    {s.pr_url && (
                      <a href={s.pr_url} target="_blank" rel="noopener noreferrer" 
                        className="inline-flex items-center gap-1 text-xs text-green-400 hover:underline">
                        <ExternalLink className="h-3 w-3" /> View PR
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </MainLayout>
  );
}
