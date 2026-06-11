# ShieldOps Enterprise Dashboard

A Next.js 14+ dashboard for the ShieldOps autonomous security remediation platform.

## Features

- **Dashboard Overview**: Real-time statistics, vulnerability trends, and activity feed
- **Repository Management**: Configure scan types, schedules, and auto-fix settings
- **Vulnerability Tracking**: Detailed vulnerability tables with filtering and actions
- **Policy Configuration**: Visual policy editor with trust boundaries and thresholds
- **Remediation Sessions**: Track automated fix attempts with detailed evidence
- **Audit Trail**: Complete audit log with export functionality
- **GitHub OAuth**: Secure authentication integration

## Tech Stack

- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- SWR for data fetching
- Recharts for visualization
- Dark theme by default

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm

### Installation

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env.local

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCKS=true
```

- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_USE_MOCKS`: Use mock data (true) or real API (false)

## Project Structure

```
dashboard/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Dashboard overview
│   ├── login/page.tsx      # GitHub OAuth login
│   ├── repos/
│   │   ├── page.tsx        # Repository list
│   │   └── [id]/page.tsx   # Repository detail
│   ├── policies/page.tsx   # Policy configuration
│   └── audit/page.tsx      # Audit trail
├── components/
│   ├── layout/             # Layout components
│   ├── dashboard/          # Dashboard widgets
│   ├── repo/               # Repository components
│   └── ui/                 # shadcn components
├── lib/
│   ├── api.ts              # API client & types
│   ├── mock-data.ts        # Development mock data
│   └── utils.ts            # Utilities
└── .env.local              # Environment config
```

## Development Mode

The dashboard includes comprehensive mock data for development:

- 5 sample repositories with various vulnerability states
- 30 days of trend data
- Realistic remediation sessions and policy decisions
- Complete audit trail with different event types

## API Integration

The dashboard is designed to work with the ShieldOps backend API. When `NEXT_PUBLIC_USE_MOCKS=false`, it connects to the real API endpoints:

- `GET /api/dashboard/overview` - Dashboard statistics
- `GET /api/repos` - Repository list
- `GET /api/vulns` - Vulnerabilities
- `GET /api/sessions` - Remediation sessions
- `PATCH /api/repos/{id}/config` - Update repository config
- And more...

## Authentication

GitHub OAuth integration for secure access:
- Development: Mock authentication (instant login)
- Production: Real GitHub OAuth flow

## Design System

- **Colors**: Dark theme with security-focused color palette
- **Typography**: Inter font for clean readability
- **Icons**: Lucide React icons throughout
- **Components**: shadcn/ui for consistent design

## Known Issues

- Production build currently has Turbopack parsing issues (development server works perfectly)
- This is a known issue with Next.js 16.2.7 and will be resolved in future versions
- Use `npm run dev` for development and testing

## Contributing

1. Follow the existing code structure
2. Use TypeScript for all new components
3. Implement proper error handling
4. Add loading states for async operations
5. Test with both mock and real API data

## License

Enterprise software - proprietary license.