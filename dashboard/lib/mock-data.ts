import { 
  Repository, 
  Vulnerability, 
  RemediationSession, 
  DashboardOverview, 
  ActivityEvent, 
  VulnTrendData, 
  AuditEvent,
  User,
  Organization
} from './api';

// Connected repositories (starts empty — user adds repos via "Connect Repo")
let mockRepositories: Repository[] = [
  // REMOVED: no pre-populated repos. User connects repos via the UI.
]; 

// All pre-populated repos moved to available pool for "Connect Repo"
const availableRepositories: Repository[] = [
  {
    id: '1',
    name: 'gaurav21/superset',
    github_url: 'https://github.com/gaurav21/superset',
    organization_id: 'org-1',
    vuln_counts: { critical: 2, high: 5, medium: 8, low: 12 },
    last_scan: '2024-06-08T15:30:00Z',
    status: 'needs_attention',
    fix_rate: 0.78,
    config: {
      scan_types: ['pip-audit', 'trivy'],
      schedule: 'daily',
      auto_fix_enabled: true,
      severity_threshold: 'medium'
    }
  },
  {
    id: '2',
    name: 'gaurav21/shieldops',
    github_url: 'https://github.com/gaurav21/shieldops',
    organization_id: 'org-1',
    vuln_counts: { critical: 0, high: 1, medium: 3, low: 5 },
    last_scan: '2024-06-09T09:15:00Z',
    status: 'healthy',
    fix_rate: 0.92,
    config: {
      scan_types: ['pip-audit', 'semgrep', 'trivy'],
      schedule: 'on-push',
      auto_fix_enabled: true,
      severity_threshold: 'high'
    }
  },
  {
    id: '3',
    name: 'org/api-gateway',
    github_url: 'https://github.com/org/api-gateway',
    organization_id: 'org-1',
    vuln_counts: { critical: 1, high: 3, medium: 6, low: 4 },
    last_scan: '2024-06-09T08:45:00Z',
    status: 'critical',
    fix_rate: 0.65,
    config: {
      scan_types: ['npm-audit', 'semgrep'],
      schedule: 'daily',
      auto_fix_enabled: false,
      severity_threshold: 'critical'
    }
  },
  {
    id: '4',
    name: 'org/auth-service',
    github_url: 'https://github.com/org/auth-service',
    organization_id: 'org-1',
    vuln_counts: { critical: 0, high: 2, medium: 4, low: 7 },
    last_scan: '2024-06-09T10:20:00Z',
    status: 'healthy',
    fix_rate: 0.85,
    config: {
      scan_types: ['pip-audit', 'trivy', 'semgrep'],
      schedule: 'weekly',
      auto_fix_enabled: true,
      severity_threshold: 'medium'
    }
  },
  {
    id: '5',
    name: 'org/frontend',
    github_url: 'https://github.com/org/frontend',
    organization_id: 'org-1',
    vuln_counts: { critical: 0, high: 0, medium: 2, low: 3 },
    last_scan: '2024-06-09T11:00:00Z',
    status: 'healthy',
    fix_rate: 0.95,
    config: {
      scan_types: ['npm-audit'],
      schedule: 'on-push',
      auto_fix_enabled: true,
      severity_threshold: 'low'
    }
  }
];

// Mock vulnerabilities
const mockVulnerabilities: Vulnerability[] = [
  {
    id: '1',
    cve_id: 'CVE-2024-1234',
    package_name: 'PyJWT',
    package_version: '2.4.0',
    severity: 'high',
    status: 'remediating',
    detected_at: '2024-06-07T14:30:00Z',
    repository_id: '1',
    title: 'JWT token validation bypass',
    description: 'Improper validation of JWT tokens could allow authentication bypass',
    fix_version: '2.8.0'
  },
  {
    id: '2',
    cve_id: 'CVE-2024-5678',
    package_name: 'Flask',
    package_version: '2.1.0',
    severity: 'critical',
    status: 'triaging',
    detected_at: '2024-06-08T09:15:00Z',
    repository_id: '1',
    title: 'Remote code execution in Flask',
    description: 'Unsafe deserialization could lead to remote code execution',
    fix_version: '3.0.0'
  },
  {
    id: '3',
    cve_id: null,
    package_name: 'lodash',
    package_version: '4.17.15',
    severity: 'medium',
    status: 'fixed',
    detected_at: '2024-06-05T11:20:00Z',
    repository_id: '3',
    title: 'Prototype pollution vulnerability',
    description: 'Prototype pollution in lodash utilities',
    fix_version: '4.17.21'
  },
  // Add more mock vulnerabilities...
];

// Mock remediation sessions
const mockSessions: RemediationSession[] = [
  {
    id: '1',
    vulnerability_id: '1',
    agent_type: 'dependency_updater',
    status: 'completed',
    started_at: '2024-06-08T10:00:00Z',
    completed_at: '2024-06-08T10:15:00Z',
    duration_seconds: 900,
    pr_url: 'https://github.com/gaurav21/superset/pull/18',
    policy_decision: 'auto_merge',
    confidence_score: 0.92,
    evidence_bundle: {
      tests_passed: true,
      breaking_changes: false,
      security_impact: 'high'
    }
  },
  {
    id: '2',
    vulnerability_id: '2',
    agent_type: 'dependency_updater',
    status: 'running',
    started_at: '2024-06-08T14:30:00Z',
    completed_at: null,
    duration_seconds: null,
    pr_url: 'https://github.com/gaurav21/superset/pull/19',
    policy_decision: 'human_review',
    confidence_score: 0.65,
    evidence_bundle: {
      tests_passed: false,
      breaking_changes: true,
      security_impact: 'critical'
    }
  }
];

// Mock dashboard overview — dynamic based on connected repos
function getMockDashboardOverview(): DashboardOverview {
  const counts = mockRepositories.reduce(
    (acc, r) => ({
      critical: acc.critical + r.vuln_counts.critical,
      high: acc.high + r.vuln_counts.high,
      medium: acc.medium + r.vuln_counts.medium,
      low: acc.low + r.vuln_counts.low,
    }),
    { critical: 0, high: 0, medium: 0, low: 0 }
  );
  return {
    total_repos: mockRepositories.length,
    repo_trend: 0,
    open_vulns: counts,
    fix_rate: mockRepositories.length > 0 ? 0.82 : 0,
    fix_rate_trend: 0,
    avg_mttr_days: mockRepositories.length > 0 ? 2.3 : 0,
    mttr_trend: 0,
  };
}
const mockDashboardOverview: DashboardOverview = getMockDashboardOverview();

// Mock activity events
const mockActivityEvents: ActivityEvent[] = [
  {
    id: '1',
    type: 'pr_merged',
    message: 'Auto-merged PR #18 for PyJWT in gaurav21/superset',
    timestamp: '2024-06-08T10:15:00Z',
    repository: 'gaurav21/superset',
    icon: '🟢',
    color: 'green'
  },
  {
    id: '2',
    type: 'human_review_needed',
    message: 'Human review needed: Flask 3.x upgrade in gaurav21/superset',
    timestamp: '2024-06-08T14:30:00Z',
    repository: 'gaurav21/superset',
    icon: '🟡',
    color: 'yellow'
  },
  {
    id: '3',
    type: 'scan_completed',
    message: 'Scan completed: 3 new vulns found in org/api-gateway',
    timestamp: '2024-06-09T08:45:00Z',
    repository: 'org/api-gateway',
    icon: '🔍',
    color: 'blue'
  },
  {
    id: '4',
    type: 'vuln_detected',
    message: 'Critical vulnerability detected in Express.js',
    timestamp: '2024-06-09T09:30:00Z',
    repository: 'org/api-gateway',
    icon: '🔴',
    color: 'red'
  },
  {
    id: '5',
    type: 'pr_merged',
    message: 'Auto-merged security patch for lodash',
    timestamp: '2024-06-09T11:00:00Z',
    repository: 'org/frontend',
    icon: '🟢',
    color: 'green'
  }
];

// Mock vulnerability trend data (last 30 days)
const mockVulnTrend: VulnTrendData[] = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - i));
  
  return {
    date: date.toISOString().split('T')[0],
    critical: Math.floor(Math.random() * 5) + 1,
    high: Math.floor(Math.random() * 15) + 5,
    medium: Math.floor(Math.random() * 30) + 15,
    low: Math.floor(Math.random() * 40) + 20
  };
});

// Mock audit events
const mockAuditEvents: AuditEvent[] = [
  {
    id: '1',
    event_type: 'scan',
    timestamp: '2024-06-09T11:00:00Z',
    actor: 'system',
    repository: 'org/frontend',
    details: { scan_type: 'npm-audit', vulns_found: 5 }
  },
  {
    id: '2',
    event_type: 'config_change',
    timestamp: '2024-06-09T10:30:00Z',
    actor: 'gaurav21',
    repository: 'gaurav21/superset',
    details: { field: 'auto_fix_enabled', old_value: false, new_value: true }
  },
  // Add more audit events...
];

// Mock user and organization
const mockUser: User = {
  id: '1',
  username: 'gaurav21',
  email: 'gaurav@example.com',
  avatar_url: 'https://github.com/gaurav21.png',
  created_at: '2024-01-01T00:00:00Z'
};

const mockOrganization: Organization = {
  id: 'org-1',
  name: 'My Organization',
  github_org: 'my-org',
  plan: 'enterprise',
  created_at: '2024-01-01T00:00:00Z'
};

// Available repos that can be connected
export function getAvailableRepos(): Repository[] {
  const connectedIds = new Set(mockRepositories.map(r => r.id));
  return availableRepositories.filter(r => !connectedIds.has(r.id));
}

// Connect a repo by ID
export function connectRepo(repoId: string): Repository | null {
  const repo = availableRepositories.find(r => r.id === repoId);
  if (repo && !mockRepositories.find(r => r.id === repoId)) {
    mockRepositories.push(repo);
    return repo;
  }
  return null;
}

// Disconnect a repo by ID
export function disconnectRepo(repoId: string): boolean {
  const idx = mockRepositories.findIndex(r => r.id === repoId);
  if (idx >= 0) {
    mockRepositories.splice(idx, 1);
    return true;
  }
  return false;
}

// Route handler for mock data
export function getMockData(url: string): any {
  // Remove query parameters for routing
  const [path] = url.split('?');
  
  switch (path) {
    case '/api/dashboard/overview':
      return getMockDashboardOverview();

    case '/api/repos/available':
      return getAvailableRepos();
    
    case '/api/dashboard/activity':
      return mockActivityEvents;
    
    case '/api/repos':
      return mockRepositories;
    
    case '/api/vulns':
      return mockVulnerabilities;
    
    case '/api/sessions':
      return mockSessions;
    
    case '/api/orgs/current':
      return mockOrganization;
    
    case '/auth/me':
      return mockUser;
    
    case '/api/dashboard/trend':
      return mockVulnTrend;
    
    case '/api/audit':
      return mockAuditEvents;
    
    default:
      // Handle dynamic routes like /api/repos/[id]
      const repoMatch = path.match(/^\/api\/repos\/(\d+)$/);
      if (repoMatch) {
        const repoId = repoMatch[1];
        return mockRepositories.find(r => r.id === repoId) || null;
      }
      
      const vulnMatch = path.match(/^\/api\/vulns\/(\d+)$/);
      if (vulnMatch) {
        const vulnId = vulnMatch[1];
        return mockVulnerabilities.find(v => v.id === vulnId) || null;
      }
      
      const sessionMatch = path.match(/^\/api\/sessions\/(\d+)$/);
      if (sessionMatch) {
        const sessionId = sessionMatch[1];
        return mockSessions.find(s => s.id === sessionId) || null;
      }
      
      throw new Error(`Mock route not found: ${url}`);
  }
}