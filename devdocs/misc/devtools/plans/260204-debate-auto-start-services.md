# 📋 [DEBATE-AUTO-START: 2026-02-04] - Auto-Start Debate Services

## References

- Spec document: `devdocs/misc/devtools/plans/debate.md`
- CLI Plan: `devdocs/misc/devtools/plans/260131-debate-cli.md`
- Server Plan: `devdocs/misc/devtools/plans/260131-debate-server.md`
- Web Overview: `devdocs/misc/devtools/common/debate-web/OVERVIEW.md`
- pnpm Workspace: `devtools/pnpm-workspace.yaml`

## User Requirements

Khi AI agent bắt đầu gọi `aw debate create`, CLI sẽ:
1. Check xem `debate-server` và `debate-web` đã start chưa
2. Nếu code chưa build → build trước
3. Nếu services chưa start → dùng pm2 để start
4. Wait và verify services ready, báo lỗi nếu không ready

## 🎯 Objective

Implement auto-start logic trong `aw debate create` CLI command để tự động khởi động debate-server và debate-web khi chưa running, đảm bảo AI agent có thể tạo debate mà không cần user manually start services.

### ⚠️ Key Considerations

1. **Production mode** - Chạy `pnpm build` + `pnpm start`, không phải dev mode
2. **pm2 ecosystem** - Dùng `ecosystem.config.js` để quản lý cả 2 services
3. **Health check required** - Verify services thực sự respond trước khi proceed
4. **Idempotent** - Nếu services đã running, không start lại
5. **Error reporting** - Nếu start fail, trả error rõ ràng cho AI agent thông báo user
6. **First-time setup** - Handle case chưa có `node_modules/` (cần `pnpm install`)

## 🔄 Implementation Plan

### Phase 1: Analysis & Preparation

- [ ] Define health check endpoints
  - **Outcome**: Server `/health`, Web check port respond
- [ ] Define pm2 ecosystem config structure
  - **Outcome**: `ecosystem.config.js` với cả 2 services
- [ ] Define build detection logic
  - **Outcome**: Check `dist/` for server, `.next/` for web

### Phase 2: Implementation (File/Code Structure)

```
devtools/common/
├── debate-server/
│   ├── ecosystem.config.cjs       # ✅ DONE - pm2 config cho cả 2 services
│   ├── package.json               # Existing
│   ├── dist/                      # Build output (check exists)
│   └── src/
│       └── routes/
│           └── health.ts          # ✅ EXISTED - Health check endpoint
│
├── debate-web/
│   ├── .next/                     # Build output (check exists)
│   └── package.json               # Existing
│
└── cli/devtool/aweave/debate/
    ├── services.py                # ✅ DONE - Service management module
    ├── config.py                  # ✅ DONE - Updated with service paths
    └── cli.py                     # ✅ DONE - Updated create + added services subcommand
```

### Phase 3: Detailed Implementation Steps

#### Step 1: Create ecosystem.config.js

File: `devtools/common/debate-server/ecosystem.config.cjs`

```javascript
module.exports = {
  apps: [
    {
      name: 'debate-server',
      cwd: __dirname,
      script: 'pnpm',
      args: 'start',
      env: {
        NODE_ENV: 'production',
        DEBATE_SERVER_PORT: 3456,
      },
      // Wait for build before start (handled by CLI)
      autorestart: true,
      max_restarts: 3,
      restart_delay: 1000,
    },
    {
      name: 'debate-web',
      cwd: require('path').join(__dirname, '../debate-web'),
      script: 'pnpm',
      args: 'start',
      env: {
        NODE_ENV: 'production',
        PORT: 3457,
        NEXT_PUBLIC_DEBATE_SERVER_URL: 'http://127.0.0.1:3456',
      },
      autorestart: true,
      max_restarts: 3,
      restart_delay: 1000,
    },
  ],
};
```

**Port Assignment:**
- debate-server: `3456` (existing)
- debate-web: `3457` (new, avoid conflict)

#### Step 2: Add Health Check Endpoint to Server

File: `devtools/common/debate-server/src/routes/health.ts`

```typescript
import { Router } from 'express';

const router = Router();

router.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'debate-server',
    timestamp: new Date().toISOString(),
  });
});

export default router;
```

Register trong `index.ts`:
```typescript
import healthRoutes from './routes/health';
app.use(healthRoutes);
```

#### Step 3: Create Service Management Module

File: `devtools/common/cli/devtool/aweave/debate/services.py`

```python
"""
Service management for debate-server and debate-web.
Handles build, start via pm2, and health checks.
"""

import os
import subprocess
import time
import httpx
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass

from aweave.mcp.response import MCPResponse, MCPError, MCPContent, ContentType


@dataclass
class ServiceConfig:
    name: str
    port: int
    cwd: Path
    build_check_path: str  # Relative to cwd
    health_url: str


# Service configurations
DEVTOOLS_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent  # devtools/common/cli/... → devtools/
DEBATE_SERVER_DIR = DEVTOOLS_ROOT / "common" / "debate-server"
DEBATE_WEB_DIR = DEVTOOLS_ROOT / "common" / "debate-web"
ECOSYSTEM_CONFIG = DEBATE_SERVER_DIR / "ecosystem.config.js"

SERVICES = {
    "debate-server": ServiceConfig(
        name="debate-server",
        port=3456,
        cwd=DEBATE_SERVER_DIR,
        build_check_path="dist",
        health_url="http://127.0.0.1:3456/health",
    ),
    "debate-web": ServiceConfig(
        name="debate-web",
        port=3457,
        cwd=DEBATE_WEB_DIR,
        build_check_path=".next",
        health_url="http://127.0.0.1:3457",  # Next.js responds on root
    ),
}

# Timeouts
BUILD_TIMEOUT = 120  # seconds
HEALTH_CHECK_TIMEOUT = 30  # seconds
HEALTH_CHECK_INTERVAL = 1  # seconds


def check_port_responding(port: int, timeout: float = 2.0) -> bool:
    """Check if a port is responding to HTTP requests."""
    try:
        response = httpx.get(f"http://127.0.0.1:{port}/", timeout=timeout)
        return response.status_code < 500
    except Exception:
        return False


def check_health_endpoint(url: str, timeout: float = 2.0) -> bool:
    """Check if health endpoint returns OK."""
    try:
        response = httpx.get(url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def is_service_running(service: ServiceConfig) -> bool:
    """Check if service is running and healthy."""
    if service.name == "debate-server":
        return check_health_endpoint(service.health_url)
    else:
        return check_port_responding(service.port)


def check_pm2_process(name: str) -> bool:
    """Check if pm2 process exists and is online."""
    try:
        result = subprocess.run(
            ["pm2", "jlist"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False
        
        import json
        processes = json.loads(result.stdout)
        for proc in processes:
            if proc.get("name") == name and proc.get("pm2_env", {}).get("status") == "online":
                return True
        return False
    except Exception:
        return False


def needs_pnpm_install(cwd: Path) -> bool:
    """Check if pnpm install is needed."""
    return not (cwd / "node_modules").exists()


def needs_build(service: ServiceConfig) -> bool:
    """Check if service needs to be built."""
    build_path = service.cwd / service.build_check_path
    return not build_path.exists()


def run_pnpm_install(cwd: Path) -> Tuple[bool, str]:
    """Run pnpm install in directory."""
    try:
        result = subprocess.run(
            ["pnpm", "install"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=BUILD_TIMEOUT,
        )
        if result.returncode != 0:
            return False, f"pnpm install failed: {result.stderr}"
        return True, ""
    except subprocess.TimeoutExpired:
        return False, f"pnpm install timed out after {BUILD_TIMEOUT}s"
    except Exception as e:
        return False, f"pnpm install error: {str(e)}"


def run_pnpm_build(service: ServiceConfig) -> Tuple[bool, str]:
    """Run pnpm build for service."""
    try:
        result = subprocess.run(
            ["pnpm", "build"],
            cwd=service.cwd,
            capture_output=True,
            text=True,
            timeout=BUILD_TIMEOUT,
        )
        if result.returncode != 0:
            return False, f"Build failed for {service.name}: {result.stderr}"
        return True, ""
    except subprocess.TimeoutExpired:
        return False, f"Build timed out for {service.name} after {BUILD_TIMEOUT}s"
    except Exception as e:
        return False, f"Build error for {service.name}: {str(e)}"


def start_services_with_pm2() -> Tuple[bool, str]:
    """Start all services using pm2 ecosystem config."""
    try:
        result = subprocess.run(
            ["pm2", "start", str(ECOSYSTEM_CONFIG)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return False, f"pm2 start failed: {result.stderr}"
        return True, ""
    except Exception as e:
        return False, f"pm2 start error: {str(e)}"


def wait_for_service_healthy(service: ServiceConfig) -> Tuple[bool, str]:
    """Wait for service to become healthy."""
    start_time = time.time()
    
    while time.time() - start_time < HEALTH_CHECK_TIMEOUT:
        if is_service_running(service):
            return True, ""
        time.sleep(HEALTH_CHECK_INTERVAL)
    
    return False, f"{service.name} did not become healthy within {HEALTH_CHECK_TIMEOUT}s"


def ensure_services() -> MCPResponse:
    """
    Ensure debate-server and debate-web are running.
    
    Steps:
    1. Check if services already running → skip if yes
    2. npm install if node_modules missing
    3. npm build if build output missing
    4. pm2 start if not running
    5. Wait for health check
    
    Returns:
        MCPResponse with success=True if services ready,
        or success=False with error details.
    """
    steps_performed = []
    
    # Check if both services already running
    server_running = is_service_running(SERVICES["debate-server"])
    web_running = is_service_running(SERVICES["debate-web"])
    
    if server_running and web_running:
        return MCPResponse(
            success=True,
            content=[MCPContent(
                type=ContentType.JSON,
                data={
                    "status": "already_running",
                    "services": {
                        "debate-server": {"port": 3456, "status": "running"},
                        "debate-web": {"port": 3457, "status": "running"},
                    },
                },
            )],
        )
    
    # Process each service that needs setup
    for name, service in SERVICES.items():
        # pnpm install if needed
        if needs_pnpm_install(service.cwd):
            steps_performed.append(f"pnpm install ({name})")
            success, error = run_pnpm_install(service.cwd)
            if not success:
                return MCPResponse(
                    success=False,
                    error=MCPError(
                        code="SERVICE_SETUP_FAILED",
                        message=error,
                        suggestion=f"Run 'cd {service.cwd} && pnpm install' manually to diagnose",
                    ),
                )
        
        # pnpm build if needed
        if needs_build(service):
            steps_performed.append(f"pnpm build ({name})")
            success, error = run_pnpm_build(service)
            if not success:
                return MCPResponse(
                    success=False,
                    error=MCPError(
                        code="SERVICE_BUILD_FAILED",
                        message=error,
                        suggestion=f"Run 'cd {service.cwd} && pnpm build' manually to diagnose",
                    ),
                )
    
    # Start services with pm2 (if not already running via pm2)
    needs_pm2_start = False
    for name, service in SERVICES.items():
        if not is_service_running(service) and not check_pm2_process(name):
            needs_pm2_start = True
            break
    
    if needs_pm2_start:
        steps_performed.append("pm2 start")
        success, error = start_services_with_pm2()
        if not success:
            return MCPResponse(
                success=False,
                error=MCPError(
                    code="SERVICE_START_FAILED",
                    message=error,
                    suggestion="Check pm2 logs: pm2 logs",
                ),
            )
    
    # Wait for services to be healthy
    for name, service in SERVICES.items():
        steps_performed.append(f"health check ({name})")
        success, error = wait_for_service_healthy(service)
        if not success:
            return MCPResponse(
                success=False,
                error=MCPError(
                    code="SERVICE_HEALTH_CHECK_FAILED",
                    message=error,
                    suggestion=f"Check logs: pm2 logs {name}",
                ),
            )
    
    return MCPResponse(
        success=True,
        content=[MCPContent(
            type=ContentType.JSON,
            data={
                "status": "started",
                "steps_performed": steps_performed,
                "services": {
                    "debate-server": {"port": 3456, "status": "running"},
                    "debate-web": {"port": 3457, "status": "running"},
                },
            },
        )],
    )
```

#### Step 4: Update CLI Config

File: `devtools/common/cli/devtool/aweave/debate/config.py`

Add service-related configs:

```python
# ... existing config ...

# Service ports
DEBATE_SERVER_PORT = int(os.getenv('DEBATE_SERVER_PORT', 3456))
DEBATE_WEB_PORT = int(os.getenv('DEBATE_WEB_PORT', 3457))

# Auto-start behavior
AUTO_START_SERVICES = os.getenv('DEBATE_AUTO_START', 'true').lower() == 'true'
```

#### Step 5: Update create.py Command

File: `devtools/common/cli/devtool/aweave/debate/commands/create.py`

Add service check at the beginning:

```python
from ..services import ensure_services
from ..config import AUTO_START_SERVICES

def command(
    debate_id: Annotated[str, typer.Option("--debate-id", help="UUID for debate")],
    title: Annotated[str, typer.Option("--title", "-t", help="Debate title")],
    # ... other params ...
):
    """Create a new debate with MOTION."""
    
    # Step 0: Ensure services are running
    if AUTO_START_SERVICES:
        service_response = ensure_services()
        if not service_response.success:
            # Output error and exit
            _output(service_response, format)
            raise typer.Exit(code=3)
        
        # Log service status (optional, for debugging)
        # service_data = service_response.content[0].data
        # if service_data.get("status") == "started":
        #     typer.echo(f"Services started: {service_data.get('steps_performed')}", err=True)
    
    # ... rest of existing create logic ...
```

#### Step 6: Add CLI Command for Manual Service Management (Optional)

File: `devtools/common/cli/devtool/aweave/debate/commands/services.py`

```python
"""Manual service management commands."""

import typer
from typing import Annotated
from ..services import ensure_services, SERVICES, is_service_running
from aweave.mcp.response import MCPResponse, MCPContent, ContentType

def status_command(
    format: Annotated[str, typer.Option("--format", "-f")] = "json",
):
    """Check status of debate services."""
    status = {}
    for name, service in SERVICES.items():
        status[name] = {
            "port": service.port,
            "running": is_service_running(service),
        }
    
    response = MCPResponse(
        success=True,
        content=[MCPContent(type=ContentType.JSON, data={"services": status})],
    )
    typer.echo(response.to_json())


def start_command(
    format: Annotated[str, typer.Option("--format", "-f")] = "json",
):
    """Start debate services (build if needed)."""
    response = ensure_services()
    typer.echo(response.to_json())
    if not response.success:
        raise typer.Exit(code=3)


def stop_command(
    format: Annotated[str, typer.Option("--format", "-f")] = "json",
):
    """Stop debate services."""
    import subprocess
    
    try:
        subprocess.run(["pm2", "stop", "debate-server", "debate-web"], capture_output=True)
        response = MCPResponse(
            success=True,
            content=[MCPContent(type=ContentType.JSON, data={"status": "stopped"})],
        )
    except Exception as e:
        response = MCPResponse(
            success=False,
            error=MCPError(code="SERVICE_STOP_FAILED", message=str(e)),
        )
    
    typer.echo(response.to_json())
    if not response.success:
        raise typer.Exit(code=3)
```

Register trong `cli.py`:

```python
from .commands import services

# Add service management subcommands
service_app = typer.Typer(help="Manage debate services")
service_app.command("status")(services.status_command)
service_app.command("start")(services.start_command)
service_app.command("stop")(services.stop_command)

app.add_typer(service_app, name="services")
```

Usage:
```bash
aw debate services status   # Check service status
aw debate services start    # Start services manually
aw debate services stop     # Stop services
```

### Phase 4: Testing

#### Manual Test Flow

```bash
# 1. Ensure clean state
pm2 delete all 2>/dev/null

# 2. Remove build outputs (test full flow)
rm -rf devtools/common/debate-server/dist
rm -rf devtools/common/debate-web/.next

# 3. Run create - should auto-build and start
aw debate generate-id
# Returns: { "content": [{ "data": { "id": "xxx" } }] }

aw debate create \
  --debate-id <id-from-above> \
  --title "Test Auto-Start" \
  --debate-type general_debate \
  --content "Test motion content"

# Expected: Services build, start, then create debate

# 4. Verify services running
pm2 list
# Should show: debate-server (online), debate-web (online)

curl http://127.0.0.1:3456/health
# Should return: { "status": "ok" }

curl http://127.0.0.1:3457
# Should return: HTML page
```

#### Integration Test Cases

| Test Case | Expected Behavior |
|-----------|-------------------|
| Services already running | Skip start, create debate |
| Services not running, built | pm2 start, wait health, create |
| Services not built | pnpm install, pnpm build, pm2 start, create |
| Build fails | Error with build output |
| Health check timeout | Error with suggestion to check logs |
| pnpm not available | Error with pnpm install suggestion |

### Phase 5: Error Codes

| Error Code | Meaning | Suggestion |
|------------|---------|------------|
| `SERVICE_SETUP_FAILED` | pnpm install failed | Run pnpm install manually |
| `SERVICE_BUILD_FAILED` | pnpm build failed | Run pnpm build manually |
| `SERVICE_START_FAILED` | pm2 start failed | Check pm2 logs |
| `SERVICE_HEALTH_CHECK_FAILED` | Service not responding | Check pm2 logs |

## 📊 Summary of Results

### ✅ Completed Achievements

- [x] Created `ecosystem.config.cjs` for pm2 (manages both services)
- [x] Created `services.py` module with ensure_services(), stop_services(), get_services_status()
- [x] Updated `config.py` with AUTO_START_SERVICES, DEBATE_SERVER_PORT, DEBATE_WEB_PORT
- [x] Updated `cli.py` - create command now auto-starts services
- [x] Added `aw debate services` subcommand group (status/start/stop)
- [x] Health endpoint already existed in debate-server (`/health`)
- [x] Tested full flow: clean state → create debate → services auto-started

## 🚧 Outstanding Issues & Follow-up

### ⚠️ Issues/Clarifications

- [x] **pm2 global install required** - ✅ Already installed
- [ ] **First run slow** - Build có thể mất 1-2 phút, cần thông báo user
- [ ] **debate-web port** - Đã assign port 3457, cần update OVERVIEW.md nếu approve
- [ ] **Health endpoint** - debate-server cần có `/health` endpoint (check server plan)
- [ ] **Disable auto-start** - User có thể set `DEBATE_AUTO_START=false` để disable
- [ ] **pnpm workspace** - Services nằm trong pnpm workspace (`devtools/pnpm-workspace.yaml`)
