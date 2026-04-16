# Geeker-Admin Project Context

## Project Overview

Geeker-Admin is a robust admin dashboard template built with Vue 3, TypeScript, and Element Plus. It features a comprehensive set of pre-built components, directives, and utility functions designed for enterprise-level application development.

## Tech Stack

- **Framework**: Vue 3 (Composition API)
- **Language**: TypeScript
- **Build Tool**: Vite
- **UI Library**: Element Plus
- **State Management**: Pinia
- **Router**: Vue Router
- **CSS Utility**: UnoCSS (Wind preset)
- **Linting/Formatting**: ESLint, Prettier, Stylelint

## Build Configuration

The project uses a custom granularity strategy for building to optimize caching:

- **Dependencies**: Split into `libs/package@version-[hash].js`.
- **Source Code**:
  - `components`: Split by directory (e.g., `components-ProTable-[hash].js`).
  - `views`: Split by page directory (e.g., `system-accountManage-[hash].js`).
  - `common`: Utils, stores, and routers are separated.
- **Vite Config**: `vite.config.ts` handles complex `manualChunks` logic, including pnpm compatibility and ignore lists for empty chunks.

## Key Directories

- `src/api`: Axios service definitions.
- `src/components`: Reusable, typed components (ProTable, Grid, etc.).
- `src/hooks`: Composable functions.
- `src/stores`: Pinia stores.
- `src/utils`: Helper functions.
- `src/views`: Page components matching route structure.

## Development Guidelines

- **Component Naming**: Use PascalCase for components.
- **Type Safety**: Ensure strict type checking with `vue-tsc`.
- **Commits**: Follow Conventional Commits specification.

## Key Components

### ProTable (`src/components/ProTable`)

A high-order component wrapping `el-table` that integrates search, pagination, and data requesting.

#### usage

```vue
<ProTable
  ref="proTable"
  page-id="SystemUser"
  :columns="columns"
  :request-api="getTableList"
  :init-param="initParam"
  :toolbar-left="['add', 'delete', 'import', 'export']"
/>
```

#### Core Props

- **pageId**: `string` (Required) - Unique ID for the table (used for column settings caching).
- **columns**: `ColumnProps[]` - Defines table columns and search form items.
  - `prop`: Field name.
  - `label`: Column header.
  - `search`: `{ el: 'input', key: '...' }` - Configures search form behavior.
  - `enum`: Dictionary data for formatting or select options.
- **requestApi**: `(params) => Promise` - Function to fetch data. `ProTable` handles loading state and parameter assembly.
- **dataCallback**: `(data) => any` - Transform data before rendering.
- **pagination**: `boolean` (Default: `true`) - Enable/disable pagination.
- **initParam**: `object` - Initial parameters passed to `requestApi`.
- **toolbarLeft**: `Array` - Configure buttons on the top left.
- **toolbarRight**: `Array` - Configure tools on the top right (refresh, setting, etc.).

#### Slots

- **Default**: Custom column content (via `bloody` scoping in `columns` or direct slot).
- **toolButton**: Custom toolbar buttons (Left side).
- **Expand**: For expandable rows.

#### Exposed Methods

- `getTableList()`: Manually trigger data refresh.
- `search()`: Trigger search (resets to page 1).
- `reset()`: Reset search form and reload.
- `element`: Access to underlying `el-table` ref.

## OpsPilot local dev (restart reminders)

- After changing **`backend/.env`** (e.g. `allowed_origins`, `database_url`, `redis_url`), **restart the FastAPI process** so settings reload.
- After changing **`frontend/.env.*`** or any **`VITE_*`** variable, **restart the Vite dev server** (`pnpm dev`).
- CORS: the UI origin must match what is listed in `allowed_origins` (both `http://localhost:8848` and `http://127.0.0.1:8848` when using that port).

### If `POST /api/v1/auth/bootstrap` returns **404**

404 means the HTTP server on that port is **not** serving OpsPilot routes (CORS would block the response without a normal 404 from FastAPI in many cases).

1. From repo: `bash backend/scripts/verify_api.sh 127.0.0.1 8000` — must show JSON with `"service":"opspilot-api"`.
2. **Port conflict:** `docker-compose.salt.yml` maps **Salt CherryPy API to host port 8000**. If Salt is running, either stop it or run OpsPilot on another port, e.g. `uvicorn app.main:app --host 127.0.0.1 --port 8001` and set **`VITE_API_URL=http://127.0.0.1:8001`** in the frontend env, then restart Vite.
3. Start the API from the **`backend/`** directory: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.
