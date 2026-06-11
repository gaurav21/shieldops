'use client';

import { Bell, Settings } from 'lucide-react';

interface TopbarProps {
  breadcrumb?: string[];
}

export function Topbar({ breadcrumb = ['Dashboard'] }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="flex items-center gap-2 text-sm">
        {breadcrumb.map((item, i) => (
          <span key={i} className="flex items-center gap-2">
            {i > 0 && <span className="text-muted-foreground">/</span>}
            <span className={i === breadcrumb.length - 1 ? 'font-medium' : 'text-muted-foreground'}>
              {item}
            </span>
          </span>
        ))}
      </nav>
      <div className="flex items-center gap-2">
        <button className="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground">
          <Bell className="h-4 w-4" />
        </button>
        <button className="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground">
          <Settings className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
