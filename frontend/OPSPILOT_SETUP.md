# OpsPilot Frontend Implementation

## Overview

This document describes the OpsPilot frontend implementation with HashiCorp design system customization and backend API integration.

## What's Been Implemented

### 1. Design System Customization ✅

**HashiCorp Theme (`src/styles/theme/hashicorp.scss`)**
- Color palette matching HashiCorp's enterprise-clean aesthetic
- Typography system with proper font families, sizes, and weights
- Spacing system based on 8px base unit
- Border radius scale (2px to 8px)
- Micro-shadows (whisper-level at 0.05 opacity)
- Dark/light mode support with CSS custom properties
- Element Plus component overrides for consistent styling

**Key Design Tokens:**
- Primary color: `#15181e` (dark charcoal)
- Accent color: `#2b89ff` (bright blue)
- Text colors: Black/charcoal for light, white/gray for dark
- Border colors: Subtle grays at 0.1-0.4 opacity
- Shadows: `rgba(97, 104, 117, 0.05) 0px 1px 1px, rgba(97, 104, 117, 0.05) 0px 2px 2px`

### 2. API Integration ✅

**API Client (`src/api/opspilot/client.ts`)**
- Axios-based HTTP client with TypeScript support
- Request interceptors for JWT token attachment
- Response interceptors for error handling
- Automatic token refresh on 401 errors
- Request cancellation for duplicate requests
- Base URL: `http://localhost:9000/api/v1`

**Type Definitions (`src/api/opspilot/types.ts`)**
- Complete TypeScript interfaces for all API responses
- Common types (ApiResponse, PaginatedResponse, ErrorResponse)
- Auth types (User, LoginRequest, RegisterRequest, etc.)
- Organization, Server, Alert, Command, Service types
- Dashboard types (DashboardStats, ServerHealthOverview, RecentAlert)

**API Modules:**
- `auth.ts` - Login, register, forgot password, token refresh
- `organizations.ts` - CRUD operations, member management
- `servers.ts` - Server management, metrics, health checks
- `alerts.ts` - Alert management, statistics, resolution
- `index.ts` - Dashboard, commands, services

### 3. Pinia Stores ✅

**OpsPilot Stores (`src/stores/modules/opspilot.ts`)**
- `useOpsPilotAuthStore` - Authentication state and actions
- `useOpsPilotOrganizationStore` - Organization management
- `useOpsPilotServerStore` - Server management
- `useOpsPilotAlertStore` - Alert management
- `useOpsPilotDashboardStore` - Dashboard data aggregation

All stores include:
- Reactive state management
- Computed properties for derived state
- Actions for data mutations
- Pinia persistence for state survival

### 4. Router Configuration ✅

**OpsPilot Router (`src/routers/opspilot.ts`)**
- Route definitions for all pages
- Auth guards (redirect to login if not authenticated)
- Navigation guards for route protection
- Progress bar integration (NProgress)
- Dynamic page titles
- Error handling

**Routes Implemented:**
- `/login` - Login page
- `/register` - Registration page
- `/forgot-password` - Password reset request
- `/dashboard` - Main dashboard
- `/servers` - Server list
- `/servers/:id` - Server detail
- `/alerts` - Alerts list
- `/organizations` - Organization list
- `/organizations/:id` - Organization detail
- `/organizations/:id/settings` - Organization settings
- `/settings` - User settings
- `/404` - Not found error
- `/500` - Server error

### 5. Auth Pages ✅

**Login Page (`src/views/auth/login/index.vue`)**
- Clean, minimal design with HashiCorp branding
- Email/password authentication
- Remember me checkbox
- Forgot password link
- Responsive design
- Dark mode support

**Register Page (`src/views/auth/register/index.vue`)**
- Email/password/confirm password fields
- Password strength requirements
- Terms of service agreement
- HashiCorp-style branding with feature highlights
- Responsive design

**Forgot Password Page (`src/views/auth/forgot-password/index.vue`)**
- Simple email input form
- Password reset link request
- Back to login navigation

### 6. Dashboard Page ✅

**Dashboard (`src/views/dashboard/index.vue`)**
- Stats cards (servers, organizations, alerts, commands)
- Server health overview with real-time metrics
- Recent alerts list with severity indicators
- Quick action buttons
- Responsive grid layout
- HashiCorp-styled components

### 7. Placeholder Pages ✅

**Coming Soon Views:**
- `/servers` - Server management interface
- `/servers/:id` - Server detail view
- `/alerts` - Alert management interface
- `/organizations` - Organization management
- `/organizations/:id` - Organization detail
- `/organizations/:id/settings` - Organization settings
- `/settings` - User settings

**Error Pages:**
- `/404` - Page not found with illustration
- `/500` - Server error with illustration

## File Structure

```
src/
├── api/
│   └── opspilot/
│       ├── client.ts          # Axios HTTP client
│       ├── types.ts           # TypeScript interfaces
│       ├── auth.ts            # Auth API
│       ├── organizations.ts   # Organization API
│       ├── servers.ts         # Server API
│       ├── alerts.ts          # Alert API
│       └── index.ts           # Dashboard & commands API
├── routers/
│   └── opspilot.ts           # Vue Router config
├── stores/
│   └── modules/
│       └── opspilot.ts        # Pinia stores
├── styles/
│   └── theme/
│       └── hashicorp.scss     # HashiCorp design system
├── views/
│   ├── auth/
│   │   ├── login/
│   │   ├── register/
│   │   └── forgot-password/
│   ├── dashboard/
│   ├── servers/
│   ├── alerts/
│   ├── organizations/
│   ├── settings/
│   └── error/
```

## Configuration

### Environment Variables

Create or update `.env.development`:

```env
VITE_API_URL=http://localhost:9000
VITE_ROUTER_MODE=hash
VITE_GLOB_APP_TITLE=OpsPilot
```

### API Base URL

The API client is configured to use:
- Development: `http://localhost:9000/api/v1`
- Production: Configured via `VITE_API_URL` environment variable

## Getting Started

### Installation

```bash
cd /Volumes/ashrul/Development/Active/opspilot/frontend
pnpm install
```

### Development Server

```bash
pnpm dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
pnpm build
```

## Testing the Integration

1. **Start the backend API:**
   ```bash
   # Ensure backend is running on http://localhost:9000
   # Check API docs at http://localhost:9000/docs
   ```

2. **Start the frontend:**
   ```bash
   pnpm dev
   ```

3. **Test authentication:**
   - Navigate to `/login`
   - Enter credentials (will be validated against backend)
   - On success, you'll be redirected to `/dashboard`

4. **Test API integration:**
   - Dashboard will fetch real data from backend
   - All API calls include JWT token in Authorization header
   - Token refresh works automatically on 401 errors

## Design System Usage

### Using HashiCorp Classes

The theme provides custom classes for HashiCorp-styled components:

```vue
<template>
  <!-- HashiCorp card -->
  <div class="hc-card">
    Content here
  </div>

  <!-- HashiCorp label -->
  <p class="hc-label">Section Label</p>

  <!-- HashiCorp heading -->
  <h2 class="hc-heading">Card Title</h2>

  <!-- HashiCorp text -->
  <p class="hc-text">Body text</p>

  <!-- HashiCorp link -->
  <a class="hc-link" href="#">Link text</a>
</template>
```

### Element Plus Components

All Element Plus components are automatically styled with HashiCorp theme:

```vue
<template>
  <!-- Primary button (dark) -->
  <el-button type="primary">Action</el-button>

  <!-- Secondary button (white) -->
  <el-button type="default">Cancel</el-button>

  <!-- Accent button (blue) -->
  <el-button type="accent">Primary Action</el-button>

  <!-- Cards with HashiCorp styling -->
  <el-card>
    <template #header>Card Title</template>
    Content
  </el-card>
</template>
```

### Custom Properties (CSS Variables)

You can use HashiCorp CSS custom properties in your components:

```css
.custom-component {
  background-color: var(--opspilot-bg-color);
  color: var(--opspilot-text-primary);
  border: 1px solid var(--opspilot-border-color);
}
```

## API Usage Examples

### Authentication

```typescript
import { useOpsPilotAuthStore } from '@/stores/modules/opspilot';

const authStore = useOpsPilotAuthStore();

// Login
await authStore.login({
  email: 'user@example.com',
  password: 'password123',
});

// Logout
await authStore.logout();

// Get current user
console.log(authStore.user);
```

### API Calls

```typescript
import { ServersAPI } from '@/api/opspilot/servers';

// List servers
const servers = await ServersAPI.list();

// Get server metrics
const metrics = await ServersAPI.getMetrics('server-id');

// Create server
const newServer = await ServersAPI.create({
  name: 'Production Server',
  hostname: 'server.example.com',
  ip_address: '192.168.1.100',
  port: 80,
  ssh_port: 22,
  os_type: 'linux',
});
```

### Store Usage

```typescript
import { useOpsPilotOrganizationStore } from '@/stores/modules/opspilot';

const orgStore = useOpsPilotOrganizationStore();

// Fetch organizations
await orgStore.fetchOrganizations();

// Get current organization
console.log(orgStore.currentOrganization);

// Create organization
const newOrg = await orgStore.createOrganization({
  name: 'My Organization',
  slug: 'my-org',
  description: 'Production servers',
});
```

## Next Steps

1. **Complete Placeholder Views:**
   - Implement server list with table, filters, and actions
   - Build server detail view with metrics charts
   - Create alert management interface with filtering
   - Develop organization management UI
   - Add user settings panel

2. **Add Advanced Features:**
   - Real-time metrics via WebSocket
   - Command execution terminal
   - Service management interface
   - Server configuration management
   - Alert rule builder

3. **Enhance Dashboard:**
   - Interactive charts (CPU, memory, network over time)
   - Server topology visualization
   - Alert trends and patterns
   - Performance heatmaps

4. **Testing:**
   - Unit tests for stores and API calls
   - Component tests with Vue Test Utils
   - E2E tests with Playwright
   - API integration tests

5. **Performance:**
   - Lazy loading for routes
   - Image optimization
   - Bundle size analysis
   - Code splitting

## Troubleshooting

### API Connection Issues

If you see connection errors:

1. Verify backend is running: `curl http://localhost:9000/health`
2. Check API docs: `http://localhost:9000/docs`
3. Verify environment variables in `.env.development`
4. Check browser console for CORS errors

### Token Refresh Failures

If tokens aren't refreshing:

1. Check that `refreshToken` is stored in Pinia
2. Verify backend refresh token endpoint is working
3. Check browser console for 401 errors
4. Ensure token isn't expired

### Styling Issues

If HashiCorp theme isn't applying:

1. Ensure `@use './theme/hashicorp' as hc;` is imported in `var.scss`
2. Check that Element Plus is imported after theme
3. Verify CSS custom properties are defined in `:root`
4. Check for CSS specificity conflicts

## Resources

- **Backend API:** http://localhost:9000/docs
- **HashiCorp Design Guide:** See `DESIGN.md` for full specifications
- **Vue 3 Docs:** https://vuejs.org/
- **Pinia Docs:** https://pinia.vuejs.org/
- **Element Plus:** https://element-plus.org/
- **Vite:** https://vitejs.dev/

## Notes

- The frontend uses hash routing for easier deployment
- All API calls are typed with TypeScript
- State persistence is handled by Pinia
- Dark mode support is built into the design system
- All components follow HashiCorp's enterprise-clean aesthetic
