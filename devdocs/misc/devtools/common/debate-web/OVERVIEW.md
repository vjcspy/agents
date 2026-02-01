# Debate Web

Next.js web application for Arbitrator to monitor debates and submit RULING/INTERVENTION.

## Purpose

Web interface cho Arbitrator (human) để:
- Monitor debates real-time qua WebSocket
- Submit INTERVENTION để pause debate
- Submit RULING để phán xử APPEAL/RESOLUTION

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Next.js 16 (App Router) |
| Styling | Tailwind CSS v4 + shadcn/ui |
| WebSocket | Native WebSocket API |
| State | React hooks (useReducer) |
| Icons | Lucide React |
| Theme | next-themes (light/dark) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         debate-web                           │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│   SIDEBAR    │              CONTENT AREA                    │
│   (240px)    │                                              │
│              │  ┌────────────────────────────────────────┐  │
│   Search     │  │  Header (title + state + connection)   │  │
│   ──────     │  ├────────────────────────────────────────┤  │
│   Debate 1   │  │  Argument List (scroll)                │  │
│   Debate 2   │  │  - ArgumentCard                        │  │
│   ...        │  │  - ArgumentCard                        │  │
│              │  │  - ...                                 │  │
│              │  ├────────────────────────────────────────┤  │
│              │  │  Action Area                           │  │
│              │  │  (INTERVENTION / RULING UI)            │  │
│              │  └────────────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────────────┘
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `NEXT_PUBLIC_DEBATE_SERVER_URL` | `http://127.0.0.1:3456` | debate-server URL |

## Project Structure

```
debate-web/
├── app/
│   ├── layout.tsx           # Root layout + ThemeProvider
│   ├── page.tsx             # Redirect to /debates
│   ├── globals.css          # Tailwind + CSS variables
│   └── debates/
│       ├── layout.tsx       # Debates layout with Sidebar
│       ├── page.tsx         # Empty state (no debate selected)
│       └── [id]/
│           └── page.tsx     # Debate detail view
├── components/
│   ├── ui/                  # shadcn components
│   ├── layout/
│   │   ├── sidebar.tsx      # Debate list sidebar
│   │   └── theme-toggle.tsx # Dark/Light mode toggle
│   ├── debate/
│   │   ├── debate-list.tsx  # Filterable debate list
│   │   ├── debate-item.tsx  # Single debate item
│   │   ├── argument-list.tsx# Scrollable argument list
│   │   ├── argument-card.tsx# Argument display card
│   │   └── action-area.tsx  # INTERVENTION/RULING UI
│   └── providers/
│       └── theme-provider.tsx
├── hooks/
│   ├── use-debate.ts        # WebSocket + debate state
│   └── use-debates-list.ts  # Debates list polling
└── lib/
    ├── types.ts             # Types from debate-server
    ├── api.ts               # REST API client
    └── utils.ts             # cn() helper
```

## Action Area Logic

| State | UI | Action |
|-------|----|--------|
| `AWAITING_OPPONENT` | Stop Button | INTERVENTION |
| `AWAITING_PROPOSER` | Stop Button | INTERVENTION |
| `AWAITING_ARBITRATOR` | Chat box | RULING |
| `INTERVENTION_PENDING` | Chat box | RULING |
| `CLOSED` | Read-only | - |

### INTERVENTION (Stop Button)

- Full-width destructive button
- Hold for 1 second to confirm (prevent accidental clicks)
- Progress indicator during hold
- Sends `submit_intervention` via WebSocket

### RULING (Chat Box)

- Textarea for ruling content
- "Close debate" checkbox
- Submit button
- Sends `submit_ruling` via WebSocket

## WebSocket Integration

### Connection

```typescript
// URL format
ws://127.0.0.1:3456/ws?debate_id=xxx

// Auto-reconnect with exponential backoff
// Max reconnect delay: 30 seconds
```

### Server → Client Events

| Event | Data | Description |
|-------|------|-------------|
| `initial_state` | `{ debate, arguments[] }` | On connect |
| `new_argument` | `{ debate, argument }` | New argument added |

### Client → Server Events

| Event | Data | Description |
|-------|------|-------------|
| `submit_intervention` | `{ debate_id, content? }` | Pause debate |
| `submit_ruling` | `{ debate_id, content, close? }` | Submit ruling |

## Development

```bash
cd devtools/common/debate-web

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

**Prerequisites:**
- debate-server running on port 3456

## Related

- **Spec:** `devdocs/misc/devtools/debate.md`
- **Server:** `devtools/common/debate-server/`
- **Server Overview:** `devdocs/misc/devtools/common/debate-server/OVERVIEW.md`
- **CLI:** `devtools/common/cli/devtool/aweave/debate/`
- **CLI Overview:** `devdocs/misc/devtools/common/cli/devtool/aweave/debate/OVERVIEW.md`
