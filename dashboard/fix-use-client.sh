#!/bin/bash

# Files that need 'use client'
files=(
  "app/login/page.tsx"
  "app/policies/page.tsx" 
  "app/repos/page.tsx"
  "app/repos/[id]/page.tsx"
  "app/audit/page.tsx"
  "components/dashboard/activity-feed.tsx"
  "components/dashboard/repos-table.tsx"
  "components/dashboard/stat-card.tsx"
  "components/dashboard/vuln-trend-chart.tsx"
  "components/layout/main-layout.tsx"
  "components/layout/sidebar.tsx"
  "components/layout/topbar.tsx"
  "components/repo/config-panel.tsx"
  "components/repo/vuln-table.tsx"
  "components/repo/session-card.tsx"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    # Remove any existing 'use client' directives
    sed -i "/^['\"]use client['\"];*$/d" "$file"
    # Add 'use client' at the top
    sed -i "1i'use client';\n" "$file"
    echo "Fixed $file"
  fi
done