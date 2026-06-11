'use client';

import React from 'react';
import useSWR from 'swr';
import { MainLayout } from '@/components/layout/main-layout';
import { StatCard } from '@/components/dashboard/stat-card';
import { fetcher, DashboardOverview, Repository, isLoggedIn } from '@/lib/api';
import { GitBranch, Shield, TrendingUp, Clock, Plus, Zap } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
  const router = useRouter();
  const { data: overview, error: overviewErr } = useSWR<DashboardOverview>('/api/dashboard/overview', fetcher);
  const { data: repos, error: reposErr } = useSWR<Repository[]>('/api/repos', fetcher);

  // Redirect to login if not authenticated
  React.useEffect(() => {
    if ((overviewErr || reposErr) && !isLoggedIn()) {
      router.push('/login');
    }
  }, [overviewErr, reposErr, router]);

  if (!overview || !repos) {
    return (
      <MainLayout title="Dashboard">
        <div className="flex items-center justify-center h-[60vh]">
          <Shield className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </MainLayout>
    );
  }

  // Empty state
  if (overview.total_repos === 0) {
    return (
      <MainLayout title="Dashboard">
        <div className="flex flex-col items-center justify-center h-[60vh]">
          <Shield className="h-16 w-16 text-green-500 mb-6" />
          <h2 className="text-2xl font-bold mb-2">Welcome to ShieldOps</h2>
          <p className="text-muted-foreground text-center mb-8 max-w-lg">
            Autonomous security remediation for your GitHub repositories.
            Connect a repo to start scanning for vulnerabilities and auto-generating fix PRs.
          </p>
          <Link
            href="/repos"
            className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-6 py-3 text-sm font-medium text-white hover:bg-green-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Connect Your First Repository
          </Link>
        </div>
      </MainLayout>
    );
  }

  const sev = overview.vulns_by_severity;

  return (
    <MainLayout title="Dashboard">
      <div className="space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Repositories"
            value={overview.total_repos}
            icon={<GitBranch className="h-4 w-4" />}
            description={`${overview.active_repos} active`}
          />
          <StatCard
            title="Vulnerabilities"
            value={overview.total_vulns}
            icon={<Shield className="h-4 w-4" />}
            description={`${sev.critical}C ${sev.high}H ${sev.medium}M ${sev.low}L`}
          />
          <StatCard
            title="Fix Rate"
            value={`${Math.round(overview.fix_rate)}%`}
            icon={<TrendingUp className="h-4 w-4" />}
          />
          <StatCard
            title="Sessions"
            value={overview.completed_sessions}
            icon={<Zap className="h-4 w-4" />}
            description={overview.active_sessions > 0 ? `${overview.active_sessions} active` : 'none active'}
          />
        </div>

        {/* Repos */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Connected Repositories</CardTitle>
            <Link
              href="/repos"
              className="inline-flex items-center gap-1 rounded-md bg-green-600/20 px-3 py-1 text-xs font-medium text-green-400 hover:bg-green-600/30"
            >
              <Plus className="h-3 w-3" /> Add Repo
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {repos.map((repo) => {
                const s = repo.vuln_summary.by_severity;
                const totalVulns = s.critical + s.high + s.medium + s.low;
                return (
                  <div key={repo.id} className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/30 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`h-2.5 w-2.5 rounded-full ${totalVulns === 0 ? 'bg-green-500' : s.critical > 0 ? 'bg-red-500' : 'bg-amber-500'}`} />
                      <div>
                        <p className="text-sm font-medium">{repo.full_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {repo.scan_config.schedule} · {repo.scan_config.scan_types.length} scanners
                          {repo.last_scan_at ? ` · Last scan ${new Date(repo.last_scan_at).toLocaleDateString()}` : ' · Never scanned'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {s.critical > 0 && <Badge variant="destructive" className="text-xs">{s.critical}C</Badge>}
                      {s.high > 0 && <Badge className="bg-amber-500/20 text-amber-400 text-xs">{s.high}H</Badge>}
                      {totalVulns === 0 && <Badge className="bg-green-500/20 text-green-400 text-xs">Clean</Badge>}
                      <Badge variant="secondary" className="text-xs">{repo.active_sessions > 0 ? `${repo.active_sessions} active` : repo.is_active ? 'Monitoring' : 'Inactive'}</Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
