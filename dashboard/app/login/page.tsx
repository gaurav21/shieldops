'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Shield } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { setToken, isLoggedIn } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [devToken, setDevToken] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (isLoggedIn()) {
      router.push('/');
    }
  }, [router]);

  const handleDevLogin = () => {
    const token = devToken.trim();
    if (!token) { setError('Enter a JWT token'); return; }
    setToken(token);
    router.push('/');
  };

  const handleGitHubLogin = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    window.location.href = `${apiUrl}/auth/github`;
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-md space-y-6 p-6">
        <div className="text-center">
          <Shield className="h-12 w-12 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold">ShieldOps</h1>
          <p className="text-muted-foreground mt-1">Autonomous Security Remediation</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sign In</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <button
              onClick={handleGitHubLogin}
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-foreground px-4 py-3 text-sm font-medium text-background hover:bg-foreground/90"
            >
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
              Sign in with GitHub
            </button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">or use dev token</span>
              </div>
            </div>

            <div className="space-y-2">
              <input
                type="text"
                placeholder="Paste JWT token..."
                value={devToken}
                onChange={e => setDevToken(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleDevLogin()}
                className="w-full rounded-lg border bg-background px-4 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <button
                onClick={handleDevLogin}
                className="w-full rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                Login with Token
              </button>
              {error && <p className="text-sm text-red-400">{error}</p>}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
