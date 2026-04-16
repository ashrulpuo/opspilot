# OpsPilot Frontend

OpsPilot DevOps Automation Platform - Frontend Application

Based on [Geeker Admin](https://github.com/Geeker-Admin/Geeker-Admin), a Vue 3 + TypeScript + Element Plus admin dashboard.

## Tech Stack

- **Framework**: Vue 3.4+
- **Language**: TypeScript 5+
- **Build Tool**: Vite 7
- **UI Library**: Element Plus
- **State Management**: Pinia
- **Routing**: Vue Router 4
- **HTTP Client**: Axios
- **Styling**: UnoCSS

## Quick Start

### Prerequisites

- Node.js 20+
- pnpm 8+

### Installation

```bash
# Install dependencies
pnpm install
```

### Development

```bash
# Start development server
pnpm dev
```

Visit http://localhost:5173

### Build for Production

```bash
# Build
pnpm build

# Preview production build
pnpm preview
```

### Testing

```bash
# Run unit tests
pnpm test

# Run E2E tests
pnpm test:e2e
```

## Project Structure

```
opspilot-frontend/
├── public/                 # Static assets
├── src/
│   ├── api/               # API client and endpoints
│   ├── assets/            # Images, fonts, icons
│   ├── components/        # Vue components
│   ├── directives/        # Custom directives
│   ├── hooks/             # Vue composition hooks
│   ├── layout/            # Layout components
│   ├── locales/           # i18n translations
│   ├── router/            # Vue Router configuration
│   ├── store/             # Pinia stores
│   ├── styles/            # Global styles
│   ├── utils/             # Utility functions
│   ├── views/             # Page components
│   ├── App.vue
│   └── main.ts
├── DESIGN.md             # HashiCorp design system
└── vite.config.ts
```

## Design System

This project uses the HashiCorp design system. See `DESIGN.md` for:
- Color palette and tokens
- Typography rules
- Component styling guidelines
- Layout principles

### Key Colors

- **Primary**: `#15181e` (dark charcoal)
- **Accent**: `#1868f2` (Vagrant blue)
- **Background**: `#ffffff` (light), `#15181e` (dark)
- **Text**: `#000000` (light), `#efeff1` (dark)

## API Configuration

Update API base URL in `src/api/config.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
```

## Environment Variables

Create `.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=OpsPilot
VITE_ENABLE_DARK_MODE=true
```

## Code Quality

```bash
# Format code
pnpm format

# Lint code
pnpm lint

# Type check
pnpm type-check
```

## Features

- [x] Vue 3 Composition API
- [x] TypeScript support
- [x] Element Plus UI components
- [x] Dark mode support
- [x] Responsive design
- [x] i18n ready
- [x] Pinia state management
- [x] ProTable component
- [ ] Organization management
- [ ] Server management
- [ ] Real-time metrics
- [ ] Web-based SSH terminal
- [ ] Alert configuration
- [ ] Log viewer

## Pages

- **Dashboard**: Overview of all servers and alerts
- **Organizations**: Manage multiple organizations
- **Servers**: Add, edit, monitor servers
- **Metrics**: Real-time and historical metrics
- **Logs**: Centralized log viewer
- **Settings**: Configuration and preferences

## Deployment

See `../opspilot-infrastructure/docker/Dockerfile.frontend` for Docker build instructions.

## License

MIT

## Credits

Based on [Geeker Admin](https://github.com/Geeker-Admin/Geeker-Admin) by [HalseySpicy](https://github.com/HalseySpicy)
