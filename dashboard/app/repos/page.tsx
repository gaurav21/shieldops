'use client';

import React, { useState } from 'react';
import useSWR, { mutate } from 'swr';
import { MainLayout } from '@/components/layout/main-layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { fetcher, Repository, searchGitHubRepos, connectRepo, GitHubRepoSearchResult } from '@/lib/api';
import Link from 'next/link';
import { GitBranch, Plus, Shield, Search, X, Loader2, Check } from 'lucide-react';

export default function ReposPage() {
  const { data: repos, error, isLoading } = useSWR<Repository[]>('/api/repos', fetcher);
  const [showConnect, setShowConnect] = useState(false);
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState<GitHubRepoSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [connectError, setConnectError] = useState('');
  const [manualInput, setManualInput] = useState('');

  const handleSearch = async (q: string) => {
    setSearch(q);
    if (q.length < 2) { setSearchResults([]); return; }
    setSearching(true);
    try {
      const results = await searchGitHubRepos(q);
      setSearchResults(results);
    } catch (e) {
      console.error('Search failed:', e);
    } finally {
      setSearching(false);
    }
  };

  const handleConnect = async (fullName: string) => {
    const [owner, repo] = fullName.split('/');
    if (!owner || !repo) { setConnectError('Enter as owner/repo'); return; }
    setConnecting(fullName);
    setConnectError('');
    try {
      await connectRepo(owner, repo);
      mutate('/api/repos');
      mutate('/api/dashboard/overview');
      // Remove from search results
      setSearchResults(prev => prev.map(r => r.full_name === fullName ? { ...r, already_connected: true } : r));
    } catch (e: any) {
      setConnectError(e.message || 'Failed to connect');
    } finally {
      setConnecting(null);
    }
  };

  const parseRepoInput = (input: string): string => {
    let clean = input.trim();
    // Handle full GitHub URLs: https://github.com/owner/repo or github.com/owner/repo
    const urlMatch = clean.match(/(?:https?:\/\/)?github\.com\/([^/]+\/[^/\s?#]+)/);
    if (urlMatch) clean = urlMatch[1];
    // Strip trailing .git
    clean = clean.replace(/\.git$/, '');
    return clean;
  };

  const handleManualConnect = () => {
    const parsed = parseRepoInput(manualInput);
    if (parsed.includes('/')) {
      handleConnect(parsed);
      setManualInput('');
    } else {
      setConnectError('Enter owner/repo or paste a GitHub URL');
    }
  };

  if (isLoading) {
    return (
      <MainLayout title="Repositories">
        <div className="flex items-center justify-center h-64">
          <Shield className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout title="Repositories">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Repositories</h2>
            <p className="text-muted-foreground">{repos?.length || 0} connected</p>
          </div>
          <button
            onClick={() => setShowConnect(!showConnect)}
            className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
          >
            {showConnect ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
            {showConnect ? 'Close' : 'Connect Repository'}
          </button>
        </div>

        {/* Connect Panel */}
        {showConnect && (
          <Card className="border-green-500/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Connect a GitHub Repository</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Manual input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="owner/repo or GitHub URL (e.g., https://github.com/gaurav21/superset)"
                  value={manualInput}
                  onChange={e => setManualInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleManualConnect()}
                  className="flex-1 rounded-lg border bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <button
                  onClick={handleManualConnect}
                  disabled={!manualInput.trim()}
                  className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                >
                  Connect
                </button>
              </div>

              {connectError && (
                <p className="text-sm text-red-400">{connectError}</p>
              )}

              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Or search your GitHub repos..."
                  value={search}
                  onChange={e => handleSearch(e.target.value)}
                  className="w-full rounded-lg border bg-background px-10 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                {searching && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />}
              </div>

              {searchResults.length > 0 && (
                <div className="space-y-1 max-h-64 overflow-y-auto">
                  {searchResults.map(r => (
                    <div key={r.github_repo_id} className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/30">
                      <div>
                        <p className="text-sm font-medium">{r.full_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {r.language || 'Unknown'} · {r.default_branch}
                          {r.description && ` · ${r.description.slice(0, 60)}`}
                        </p>
                      </div>
                      {r.already_connected ? (
                        <Badge className="bg-green-500/20 text-green-400 text-xs"><Check className="h-3 w-3 mr-1" />Connected</Badge>
                      ) : (
                        <button
                          onClick={() => handleConnect(r.full_name)}
                          disabled={connecting === r.full_name}
                          className="inline-flex items-center gap-1 rounded-md bg-green-600/20 px-3 py-1 text-xs font-medium text-green-400 hover:bg-green-600/30 disabled:opacity-50"
                        >
                          {connecting === r.full_name ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
                          Connect
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Empty State */}
        {(!repos || repos.length === 0) && !showConnect && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <GitBranch className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No repositories connected</h3>
              <p className="text-muted-foreground text-center mb-6 max-w-md">
                Connect your GitHub repositories to start autonomous security remediation.
              </p>
              <button
                onClick={() => setShowConnect(true)}
                className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-6 py-3 text-sm font-medium text-white hover:bg-green-700"
              >
                <Plus className="h-4 w-4" />
                Connect Your First Repository
              </button>
            </CardContent>
          </Card>
        )}

        {/* Connected Repos */}
        {repos && repos.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {repos.map(repo => {
              const s = repo.vuln_summary.by_severity;
              const totalVulns = s.critical + s.high + s.medium + s.low;
              return (
                <Link key={repo.id} href={`/repos/${repo.id}`}>
                  <Card className="hover:border-foreground/20 transition-colors cursor-pointer h-full">
                    <CardHeader className="flex flex-row items-center gap-3 pb-2">
                      <div className={`h-3 w-3 rounded-full ${totalVulns === 0 ? 'bg-green-500' : s.critical > 0 ? 'bg-red-500' : 'bg-amber-500'}`} />
                      <CardTitle className="text-sm font-medium truncate">{repo.full_name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-1 mb-3">
                        {s.critical > 0 && <Badge variant="destructive" className="text-xs">{s.critical} Critical</Badge>}
                        {s.high > 0 && <Badge className="bg-amber-500/20 text-amber-400 text-xs">{s.high} High</Badge>}
                        {s.medium > 0 && <Badge className="bg-blue-500/20 text-blue-400 text-xs">{s.medium} Med</Badge>}
                        {totalVulns === 0 && <Badge className="bg-green-500/20 text-green-400 text-xs">✓ Clean</Badge>}
                      </div>
                      <div className="text-xs text-muted-foreground space-y-1">
                        <p>{repo.scan_config.schedule} · {repo.scan_config.scan_types.join(', ')}</p>
                        <p>{repo.last_scan_at ? `Last scan: ${new Date(repo.last_scan_at).toLocaleDateString()}` : 'Never scanned'}</p>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
