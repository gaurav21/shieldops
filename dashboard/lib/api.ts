// ── Types matching real backend API ──

export interface Repository {
  id: string;
  github_repo_id: number;
  full_name: string;
  default_branch: string;
  is_active: boolean;
  last_scan_at: string | null;
  next_scan_at: string | null;
  vuln_summary: {
    total: number;
    by_severity: { low: number; medium: number; high: number; critical: number };
    by_status: Record<string, number>;
  };
  active_sessions: number;
  scan_config: {
    scan_types: string[];
    schedule: string;
    auto_fix: boolean;
    excluded_paths: string[];
    severity_threshold: string;
  };
  policy_overrides: Record<string, any>;
}

export interface DashboardOverview {
  total_repos: number;
  active_repos: number;
  total_vulns: number;
  vulns_by_severity: { low: number; medium: number; high: number; critical: number };
  vulns_by_status: Record<string, number>;
  fix_rate: number;
  mttr_hours: number;
  active_sessions: number;
  completed_sessions: number;
  total_acu_cost: number;
  trend_data: {
    vulnerabilities: { date: string; count: number }[];
    sessions: { date: string; count: number }[];
  };
}

export interface GitHubRepoSearchResult {
  github_repo_id: number;
  full_name: string;
  description: string | null;
  language: string | null;
  default_branch: string;
  already_connected: boolean;
}

export interface Vulnerability {
  id: string;
  cve_id: string | null;
  package_name: string;
  current_version: string | null;
  fixed_version: string | null;
  severity: string;
  status: string;
  title: string;
  reachable: boolean | null;
  github_issue_number: number | null;
  first_detected_at: string;
  resolved_at: string | null;
}

export interface RemediationSession {
  id: string;
  agent_type: string;
  status: string;
  policy_decision: string | null;
  pr_url: string | null;
  duration_seconds: number | null;
  acu_cost: number | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface ActivityEvent {
  id: string;
  type: string;
  message: string;
  timestamp: string;
  repository?: string;
  icon: string;
  color: string;
}

export interface VulnTrendData {
  date: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  actor: string;
  timestamp: string;
  repository?: string;
  details: Record<string, any>;
}

export interface User {
  id: string;
  login: string;
  email: string;
  avatar_url: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
}

// ── API Client ──

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('shieldops_token');
}

export function setToken(token: string) {
  localStorage.setItem('shieldops_token', token);
}

export function clearToken() {
  localStorage.removeItem('shieldops_token');
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Don't add trailing slash — some endpoints 307 redirect and drop auth
  const url = `${API_BASE_URL}${path}`;

  const resp = await fetch(url, {
    ...options,
    headers,
    redirect: 'follow',
  });

  if (resp.status === 401) {
    clearToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  return resp;
}

// SWR fetcher
export async function fetcher(path: string): Promise<any> {
  const resp = await apiFetch(path);
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status}`);
  }
  return resp.json();
}

// ── API Methods ──

export async function searchGitHubRepos(query: string): Promise<GitHubRepoSearchResult[]> {
  const resp = await apiFetch(`/api/repos/search/?q=${encodeURIComponent(query)}`);
  if (!resp.ok) throw new Error(`Search failed: ${resp.status}`);
  return resp.json();
}

export async function connectRepo(owner: string, repo: string): Promise<Repository> {
  const resp = await apiFetch('/api/repos/connect/', {
    method: 'POST',
    body: JSON.stringify({ owner, repo }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `Connect failed: ${resp.status}`);
  }
  return resp.json();
}

export async function disconnectRepo(repoId: string): Promise<void> {
  await apiFetch(`/api/repos/${repoId}/deactivate`, { method: 'POST' });
}
