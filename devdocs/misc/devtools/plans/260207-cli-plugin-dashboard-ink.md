# 260207 - CLI Plugin Dashboard (Ink v6)

## References

- `devdocs/misc/devtools/OVERVIEW.md` — Global devtools overview
- `devdocs/misc/devtools/common/cli/OVERVIEW.md` — oclif CLI entrypoint
- `devdocs/misc/devtools/common/cli-plugin-debate/OVERVIEW.md` — Existing plugin pattern reference
- `devtools/common/cli/package.json` — Root CLI oclif config
- `devtools/pnpm-workspace.yaml` — Workspace packages
- Ink v6 docs: https://github.com/vadimdemedes/ink
- oclif ESM docs: https://oclif.github.io/docs/esm

## User Requirements

1. Sử dụng Ink v6 (ESM-only, React 19)
2. Scope dashboard: Real data (pm2, system info, health checks, workspace scan)
3. Command structure: Option B — Multiple commands (`aw dashboard`, `aw dashboard services`, etc.)
4. Mục đích: Sample CLI module thể hiện integration oclif + Ink, showcase đầy đủ tính năng Ink v6

## 🎯 Objective

Tạo oclif plugin `@aweave/cli-plugin-dashboard` sử dụng Ink v6 để build interactive terminal dashboard hiển thị real data từ hệ thống devtools. Plugin này vừa là công cụ monitoring thực tế, vừa là reference implementation cho việc tích hợp Ink vào oclif plugin ecosystem.

### ⚠️ Key Considerations

1. **ESM + CJS Interop**: Plugin là ESM (`"type": "module"`), root CLI (`@aweave/cli`) là CJS. oclif v4 hỗ trợ CJS root load ESM plugin, nhưng linked ESM plugin PHẢI được compile trước (`pnpm build`) — không hỗ trợ ts-node dev mode.

2. **Không dùng community Ink packages**: `ink-spinner`, `ink-table`, `ink-big-text`... đều có peer dep `ink ^4` hoặc `^5`, conflict với Ink v6/React 19. Tự build custom components từ Ink primitives — vừa showcase Ink tốt hơn, vừa zero conflicts.

3. **Không cần `@aweave/cli-shared`**: Dashboard là interactive UI, không output MCPResponse format cho AI agents. Dependency tree minimal: chỉ `@oclif/core` + `ink` + `react`.

4. **Real data reliability**: pm2, server health check có thể không available — mọi data source cần graceful fallback (show "unavailable" thay vì crash).

5. **Terminal compatibility**: Dashboard dùng Unicode characters (box drawing, progress blocks, sparkline) — cần fallback cho terminals không hỗ trợ full Unicode.

## 🔄 Implementation Plan

### Phase 1: Analysis & Preparation

- [ ] Verify oclif v4 + ESM plugin interop
  - **Outcome**: Confirm CJS root CLI loads ESM plugin thành công
- [ ] Define Ink v6 component API surface cần sử dụng
  - **Outcome**: Box, Text, Newline, Spacer, Static, Transform, useInput, useFocus, useFocusManager, useApp, useStdout, useState, useEffect
- [ ] Define real data sources + fallback strategy
  - **Outcome**: pm2 jlist, os module, fetch health, fs workspace scan — tất cả có try/catch fallback
- [ ] Xác nhận dependency versions
  - **Outcome**: ink@^6.6.0, react@^19.0.0, @oclif/core@^4.2.8, @types/react@^19.0.0

### Phase 2: Implementation (File/Code/Test Structure)

```
devtools/common/cli-plugin-dashboard/           # 🚧 TODO - New ESM oclif plugin
├── package.json                                # "type": "module", oclif + ink + react
├── tsconfig.json                               # module: Node16, jsx: react-jsx
└── src/
    ├── index.ts                                # Empty (oclif auto-discovers commands)
    ├── commands/
    │   └── dashboard/
    │       ├── index.ts                        # aw dashboard — full interactive dashboard
    │       ├── services.ts                     # aw dashboard services — pm2 + health
    │       ├── system.ts                       # aw dashboard system — CPU/mem/disk
    │       ├── workspace.ts                    # aw dashboard workspace — packages status
    │       └── logs.ts                         # aw dashboard logs — live log stream
    ├── components/
    │   ├── Dashboard.tsx                       # Root: Header + TabBar + active panel
    │   ├── Header.tsx                          # Title + clock + version
    │   ├── TabBar.tsx                          # Tab navigation bar
    │   ├── panels/
    │   │   ├── ServicesPanel.tsx               # pm2 process list + health checks
    │   │   ├── SystemPanel.tsx                 # CPU/memory/disk progress bars + sparkline
    │   │   ├── WorkspacePanel.tsx              # Package tree + build status
    │   │   └── LogsPanel.tsx                   # Live pm2 log feed
    │   └── shared/
    │       ├── Table.tsx                       # Custom table (Box grid layout)
    │       ├── ProgressBar.tsx                 # ████░░░░ 65%
    │       ├── Spinner.tsx                     # ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏ frame animation
    │       ├── StatusBadge.tsx                 # ● online / ✗ offline (color-coded)
    │       └── Sparkline.tsx                   # ▁▂▃▅▇ mini chart
    ├── hooks/
    │   ├── useInterval.ts                      # setInterval wrapper (auto-cleanup)
    │   ├── useServices.ts                      # pm2 data + health check fetcher
    │   ├── useSystemInfo.ts                    # CPU/memory/disk polling
    │   ├── useWorkspace.ts                     # Workspace package scanner
    │   └── useLogs.ts                          # pm2 log stream reader
    └── lib/
        ├── pm2.ts                              # pm2 jlist parser + log reader
        ├── system.ts                           # os module wrappers, df, versions
        └── health.ts                           # fetch() health endpoint checker
```

### Phase 3: Detailed Implementation Steps

#### Step 1: Scaffold Package + ESM Config

- [ ] Create `devtools/common/cli-plugin-dashboard/package.json`:
  ```json
  {
    "name": "@aweave/cli-plugin-dashboard",
    "version": "0.1.0",
    "private": true,
    "type": "module",
    "main": "dist/index.js",
    "types": "dist/index.d.ts",
    "scripts": { "build": "tsc" },
    "oclif": {
      "commands": "./dist/commands",
      "topicSeparator": " "
    },
    "dependencies": {
      "@oclif/core": "^4.2.8",
      "ink": "^6.6.0",
      "react": "^19.0.0"
    },
    "devDependencies": {
      "@types/react": "^19.0.0",
      "@types/node": "^22.10.7",
      "typescript": "^5.7.3"
    }
  }
  ```
- [ ] Create `tsconfig.json`:
  ```json
  {
    "compilerOptions": {
      "declaration": true,
      "module": "Node16",
      "moduleResolution": "node16",
      "outDir": "dist",
      "rootDir": "src",
      "strict": true,
      "target": "es2022",
      "jsx": "react-jsx",
      "esModuleInterop": true,
      "skipLibCheck": true
    },
    "include": ["./src/**/*"]
  }
  ```
- [ ] Create empty `src/index.ts`
- [ ] Add to `devtools/pnpm-workspace.yaml`: `common/cli-plugin-dashboard`
- [ ] Add to `devtools/common/cli/package.json`:
  - dependency: `"@aweave/cli-plugin-dashboard": "workspace:*"`
  - oclif.plugins: add `"@aweave/cli-plugin-dashboard"`
- [ ] `pnpm install` → verify dependency resolution

#### Step 2: Build Shared Components

- [ ] `Spinner.tsx` — Frame animation với useEffect interval, configurable spinner styles
- [ ] `ProgressBar.tsx` — Props: value (0-100), width, label, color. Render: `████░░░░ 65%`
- [ ] `StatusBadge.tsx` — Props: status ('online'|'offline'|'loading'). Render: colored `●`/`✗`/`◌`
- [ ] `Table.tsx` — Props: columns[], rows[]. Box-based grid với header row, alignment, borders
- [ ] `Sparkline.tsx` — Props: data number[], width. Render: `▁▂▃▅▇` normalized to range

#### Step 3: Build Data Hooks + Lib

- [ ] `lib/pm2.ts` — `getPm2Processes()`: exec `pm2 jlist`, parse JSON, return typed array
- [ ] `lib/pm2.ts` — `getPm2Logs(lines)`: exec `pm2 logs --nostream --lines N`, parse output
- [ ] `lib/system.ts` — `getCpuUsage()`: os.cpus() delta calculation over interval
- [ ] `lib/system.ts` — `getMemoryUsage()`: os.totalmem/freemem → percentage + formatted
- [ ] `lib/system.ts` — `getDiskUsage()`: exec `df -h /` → parse
- [ ] `lib/system.ts` — `getVersions()`: node version, pnpm version, os info
- [ ] `lib/health.ts` — `checkHealth(url, timeout)`: fetch with AbortController timeout
- [ ] `hooks/useInterval.ts` — Generic interval hook: `useInterval(callback, delayMs)`
- [ ] `hooks/useServices.ts` — Combines pm2 + health, polls every 5s
- [ ] `hooks/useSystemInfo.ts` — CPU/mem/disk, polls every 2s, maintains sparkline history
- [ ] `hooks/useWorkspace.ts` — Scan once on mount: read pnpm-workspace.yaml, check dist/ exists
- [ ] `hooks/useLogs.ts` — Poll pm2 logs every 3s, maintain rolling buffer (last 50 lines)

#### Step 4: Build Panels

- [ ] `ServicesPanel.tsx`:
  - PM2 Processes table: Name, Status (StatusBadge), CPU%, Memory, Uptime
  - Health Checks table: Endpoint, URL, Status (StatusBadge), Latency
  - Auto-refresh indicator (Spinner + "Refreshing..." khi đang fetch)
- [ ] `SystemPanel.tsx`:
  - CPU: ProgressBar + Sparkline (last 30 readings)
  - Memory: ProgressBar + used/total text
  - Disk: ProgressBar + used/total text
  - Info box: Node version, pnpm version, OS, hostname, uptime
- [ ] `WorkspacePanel.tsx`:
  - Package list: Name, Path, Build Status (✓ dist/ exists / ✗ not built)
  - Dependency count per package
  - Total packages summary
- [ ] `LogsPanel.tsx`:
  - Static component cho log history (không re-render old lines)
  - Color-coded: INFO=cyan, ERROR=red, WARN=yellow
  - Auto-scroll to bottom
  - Line format: `[timestamp] [service] message`

#### Step 5: Build Dashboard Shell

- [ ] `Header.tsx`:
  - Title: "AWeave DevTools" (bold, colored)
  - Clock: real-time HH:MM:SS (useEffect interval 1s)
  - Version: from package.json
- [ ] `TabBar.tsx`:
  - Tabs: Services | System | Workspace | Logs
  - Active tab: bold + underline + color
  - Inactive: dim
  - Show keyboard hint: `[Tab]` or `[1-4]`
- [ ] `Dashboard.tsx`:
  - State: activeTab (useState)
  - useInput: Tab/1-4 switch tabs, q quit, r force refresh
  - useApp: exit() on q
  - useStdout: get terminal width for responsive layout
  - Render: Header → TabBar → active panel component
  - Pass refresh signal to active panel

#### Step 6: Wire oclif Commands

- [ ] `commands/dashboard/index.ts`:
  - oclif Command class
  - `run()`: `const {render} = await import('ink'); render(<Dashboard />);`
  - Flags: `--refresh-interval` (default 5s)
- [ ] `commands/dashboard/services.ts`:
  - Render only ServicesPanel (standalone, không cần tab nav)
  - Flags: `--watch` (continuous) vs one-shot
- [ ] `commands/dashboard/system.ts`:
  - Render only SystemPanel
  - Flags: `--watch`
- [ ] `commands/dashboard/workspace.ts`:
  - Render only WorkspacePanel
  - One-shot (no watch needed — static data)
- [ ] `commands/dashboard/logs.ts`:
  - Render only LogsPanel
  - Flags: `--lines` (default 50), `--service` (filter by pm2 service name)

#### Step 7: Integration + Polish

- [ ] Register plugin in root CLI (already done in Step 1 config)
- [ ] `pnpm install && pnpm build` (full workspace)
- [ ] Test: `aw dashboard` — verify full dashboard works
- [ ] Test: `aw dashboard services` — verify standalone panel
- [ ] Test: `aw dashboard system` — verify system info
- [ ] Test: `aw dashboard workspace` — verify workspace scan
- [ ] Test: `aw dashboard logs` — verify log stream
- [ ] Responsive: test with narrow terminal (< 80 cols) — graceful degradation
- [ ] Error handling: test with pm2 not running, server down, no build artifacts

### Ink v6 Features Coverage Matrix

| Ink Feature | Component/Hook | Status |
|-------------|---------------|--------|
| `Box` (border, padding, flexDirection) | Every panel, Dashboard layout | 🚧 |
| `Box` (justifyContent, alignItems, flexGrow) | Dashboard grid, Table | 🚧 |
| `Text` (color, bold, dim) | StatusBadge, headers, data | 🚧 |
| `Text` (italic, underline, strikethrough) | TabBar active, warnings | 🚧 |
| `Newline` | Panel spacing | 🚧 |
| `Spacer` | Header layout (title ←→ clock) | 🚧 |
| `Static` | LogsPanel (non-rerendering log history) | 🚧 |
| `Transform` | Log line colorization | 🚧 |
| `useInput` | Tab nav, quit, refresh, scroll | 🚧 |
| `useFocus` / `useFocusManager` | Panel focus switching | 🚧 |
| `useApp` (exit) | Quit handling (q key) | 🚧 |
| `useStdout` (dimensions) | Responsive layout | 🚧 |
| `useState` + `useEffect` | All data hooks, clock | 🚧 |
| Custom Spinner | Spinner.tsx (frame animation) | 🚧 |
| Custom ProgressBar | SystemPanel (CPU/mem/disk) | 🚧 |
| Custom Table | ServicesPanel, WorkspacePanel | 🚧 |
| Custom Sparkline | SystemPanel (CPU history) | 🚧 |
| Custom StatusBadge | ServicesPanel (online/offline) | 🚧 |

### Real Data Sources

| Data | Source | Method | Fallback |
|------|--------|--------|----------|
| PM2 processes | `pm2 jlist` | `child_process.execSync` | Empty list + "pm2 not available" |
| Server health | `http://127.0.0.1:3456/health` | `fetch()` | Status: offline |
| Debate-web health | `http://127.0.0.1:3457` | `fetch()` | Status: offline |
| CPU usage | `os.cpus()` | Compute delta over interval | 0% |
| Memory | `os.totalmem()` / `os.freemem()` | Direct call | Show raw numbers |
| Disk | `df -h /` | `child_process.execSync` | "unavailable" |
| Node version | `process.version` | Direct | Always available |
| pnpm version | `pnpm --version` | `child_process.execSync` | "unknown" |
| Workspace packages | `pnpm-workspace.yaml` + `fs` | Read YAML + scan `dist/` | Empty list |
| PM2 logs | `pm2 logs --nostream` | `child_process.execSync` | "No logs available" |
| Git activity | `git log --oneline -10` | `child_process.execSync` | "No git history" |

### Command Reference

| Command | Description | Flags |
|---------|-------------|-------|
| `aw dashboard` | Full interactive dashboard with tab navigation | `--refresh-interval <seconds>` |
| `aw dashboard services` | PM2 processes + health checks | `--watch` |
| `aw dashboard system` | CPU, memory, disk, versions | `--watch` |
| `aw dashboard workspace` | Workspace packages + build status | (none — one-shot) |
| `aw dashboard logs` | Live PM2 log stream | `--lines <n>`, `--service <name>` |

### Dashboard Visual Target

**Services Tab:**
```
┌──────────────────── AWeave DevTools ─── 14:32:05 ──────────────────────┐
│                                                                         │
│  ▸ Services    System    Workspace    Logs                              │
│ ─────────────────────────────────────────────────────────────────────── │
│                                                                         │
│  ┌─ PM2 Processes ──────────────────────────────────────────────────┐  │
│  │  Name              Status    CPU     Memory     Uptime           │  │
│  │  aweave-server     ● online  2.1%    48.2 MB    2d 5h           │  │
│  │  debate-web        ● online  0.3%    32.1 MB    2d 5h           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ Health Checks ──────────────────────────────────────────────────┐  │
│  │  Server API    http://127.0.0.1:3456    ● healthy    12ms       │  │
│  │  Debate Web    http://127.0.0.1:3457    ● healthy    8ms        │  │
│  │  WebSocket     ws://127.0.0.1:3456/ws   ✗ offline    —          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [Tab] switch  [↑↓] scroll  [r] refresh  [q] quit                     │
└─────────────────────────────────────────────────────────────────────────┘
```

**System Tab:**
```
┌──────────────────── AWeave DevTools ─── 14:32:05 ──────────────────────┐
│                                                                         │
│  Services    ▸ System    Workspace    Logs                              │
│ ─────────────────────────────────────────────────────────────────────── │
│                                                                         │
│  ┌─ Resources ──────────────────────────────────────────────────────┐  │
│  │  CPU    ████████████░░░░░░░░  58%    ▁▂▃▅▇▅▃▂▁▃▅▇▅▃           │  │
│  │  MEM    ██████████████░░░░░░  72%    11.5 GB / 16.0 GB         │  │
│  │  DISK   ████████░░░░░░░░░░░░  41%    195 GB / 476 GB           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─ Environment ────────────────────────────────────────────────────┐  │
│  │  Node.js     v20.11.0                                           │  │
│  │  pnpm        10.2.0                                             │  │
│  │  OS          darwin 24.6.0 (arm64)                              │  │
│  │  Hostname    kais-macbook                                       │  │
│  │  Uptime      5d 12h 30m                                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [Tab] switch  [↑↓] scroll  [r] refresh  [q] quit                     │
└─────────────────────────────────────────────────────────────────────────┘
```

**Workspace Tab:**
```
┌──────────────────── AWeave DevTools ─── 14:32:05 ──────────────────────┐
│                                                                         │
│  Services    System    ▸ Workspace    Logs                              │
│ ─────────────────────────────────────────────────────────────────────── │
│                                                                         │
│  ┌─ Packages (10) ─────────────────────────────────────────────────┐  │
│  │  Package                        Path                    Built   │  │
│  │  @aweave/cli                    common/cli/             ✓       │  │
│  │  @aweave/cli-shared             common/cli-shared/      ✓       │  │
│  │  @aweave/cli-plugin-debate      common/cli-plugin-...   ✓       │  │
│  │  @aweave/cli-plugin-docs        common/cli-plugin-...   ✓       │  │
│  │  @aweave/cli-plugin-dashboard   common/cli-plugin-...   ✗       │  │
│  │  @aweave/server                 common/server/          ✓       │  │
│  │  @aweave/nestjs-debate          common/nestjs-debate/   ✓       │  │
│  │  @aweave/debate-machine         common/debate-machine/  ✓       │  │
│  │  debate-web                     common/debate-web/      ✓       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Summary: 9/10 built  ·  Last scan: 14:32:05                          │
│                                                                         │
│  [Tab] switch  [↑↓] scroll  [r] refresh  [q] quit                     │
└─────────────────────────────────────────────────────────────────────────┘
```

**Logs Tab:**
```
┌──────────────────── AWeave DevTools ─── 14:32:05 ──────────────────────┐
│                                                                         │
│  Services    System    Workspace    ▸ Logs                              │
│ ─────────────────────────────────────────────────────────────────────── │
│                                                                         │
│  14:31:42  aweave-server  INFO   Request POST /debates                 │
│  14:31:42  aweave-server  INFO   Response 201 Created (12ms)           │
│  14:31:45  debate-web     INFO   WebSocket connected                   │
│  14:31:50  aweave-server  INFO   Request GET /debates/abc-123          │
│  14:31:50  aweave-server  INFO   Response 200 OK (3ms)                 │
│  14:32:01  aweave-server  WARN   Poll timeout for debate xyz-789       │
│  14:32:05  debate-web     ERROR  WebSocket disconnected                │
│                                                                         │
│                                                                         │
│                                                                         │
│                                                                         │
│  Showing last 50 lines  ·  Auto-refresh: 3s                           │
│                                                                         │
│  [Tab] switch  [↑↓] scroll  [r] refresh  [q] quit                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📊 Summary of Results

> Do not summarize the results until the implementation is done and I request it

### ✅ Completed Achievements

- (pending implementation)

## 🚧 Outstanding Issues & Follow-up

### ⚠️ Issues/Clarifications

- [ ] Verify oclif v4 CJS root + ESM plugin interop thực tế (Step 1 phải test trước khi build toàn bộ)
- [ ] ink-spinner, ink-table community packages peer dep conflict với Ink v6 — decision: build custom components
- [ ] `pm2 jlist` output format cần verify trên máy hiện tại (pm2 version specific)
- [ ] Terminal minimum width assumption (80 cols) — cần test narrow terminals
