"""
Service management for debate-server and debate-web.

Handles build, start via pm2, and health checks.
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from aweave.mcp.response import ContentType, MCPContent, MCPError, MCPResponse


@dataclass
class ServiceConfig:
    """Configuration for a debate service."""

    name: str
    port: int
    cwd: Path
    build_check_path: str  # Relative to cwd
    health_url: str


# Path resolution
# devtools/common/cli/devtool/aweave/debate/services.py -> devtools/
_THIS_FILE = Path(__file__).resolve()
DEVTOOLS_ROOT = _THIS_FILE.parent.parent.parent.parent.parent.parent
DEBATE_SERVER_DIR = DEVTOOLS_ROOT / "common" / "debate-server"
DEBATE_WEB_DIR = DEVTOOLS_ROOT / "common" / "debate-web"
ECOSYSTEM_CONFIG = DEBATE_SERVER_DIR / "ecosystem.config.cjs"

# Service configurations
SERVICES: dict[str, ServiceConfig] = {
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
        health_url="http://127.0.0.1:3457",
    ),
}

# Timeouts
BUILD_TIMEOUT = 180  # seconds (Next.js build can take a while)
HEALTH_CHECK_TIMEOUT = 30  # seconds
HEALTH_CHECK_INTERVAL = 1  # seconds


def _check_port_responding(port: int, timeout: float = 2.0) -> bool:
    """Check if a port is responding to HTTP requests."""
    try:
        response = httpx.get(f"http://127.0.0.1:{port}/", timeout=timeout)
        return response.status_code < 500
    except Exception:
        return False


def _check_health_endpoint(url: str, timeout: float = 2.0) -> bool:
    """Check if health endpoint returns OK."""
    try:
        response = httpx.get(url, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def is_service_running(service: ServiceConfig) -> bool:
    """Check if service is running and healthy."""
    if service.name == "debate-server":
        return _check_health_endpoint(service.health_url)
    else:
        return _check_port_responding(service.port)


def _check_pm2_process(name: str) -> bool:
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

        processes = json.loads(result.stdout)
        for proc in processes:
            if proc.get("name") == name and proc.get("pm2_env", {}).get("status") == "online":
                return True
        return False
    except Exception:
        return False


def _needs_install(cwd: Path) -> bool:
    """Check if pnpm install is needed."""
    return not (cwd / "node_modules").exists()


def _needs_build(service: ServiceConfig) -> bool:
    """Check if service needs to be built."""
    build_path = service.cwd / service.build_check_path
    return not build_path.exists()


def _run_pnpm_install(cwd: Path) -> tuple[bool, str]:
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
    except FileNotFoundError:
        return False, "pnpm not found. Please install pnpm: npm install -g pnpm"
    except Exception as e:
        return False, f"pnpm install error: {e!s}"


def _run_pnpm_build(service: ServiceConfig) -> tuple[bool, str]:
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
    except FileNotFoundError:
        return False, "pnpm not found. Please install pnpm: npm install -g pnpm"
    except Exception as e:
        return False, f"Build error for {service.name}: {e!s}"


def _start_services_with_pm2() -> tuple[bool, str]:
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
    except FileNotFoundError:
        return False, "pm2 not found. Please install pm2: npm install -g pm2"
    except Exception as e:
        return False, f"pm2 start error: {e!s}"


def _wait_for_service_healthy(service: ServiceConfig) -> tuple[bool, str]:
    """Wait for service to become healthy."""
    start_time = time.time()

    while time.time() - start_time < HEALTH_CHECK_TIMEOUT:
        if is_service_running(service):
            return True, ""
        time.sleep(HEALTH_CHECK_INTERVAL)

    return False, f"{service.name} did not become healthy within {HEALTH_CHECK_TIMEOUT}s"


def get_services_status() -> dict[str, Any]:
    """Get status of all services."""
    status = {}
    for name, service in SERVICES.items():
        running = is_service_running(service)
        pm2_online = _check_pm2_process(name)
        status[name] = {
            "port": service.port,
            "running": running,
            "pm2_online": pm2_online,
            "needs_build": _needs_build(service),
            "needs_install": _needs_install(service.cwd),
        }
    return status


def ensure_services() -> MCPResponse:
    """
    Ensure debate-server and debate-web are running.

    Steps:
    1. Check if services already running -> skip if yes
    2. pnpm install if node_modules missing
    3. pnpm build if build output missing
    4. pm2 start if not running
    5. Wait for health check

    Returns:
        MCPResponse with success=True if services ready,
        or success=False with error details.
    """
    steps_performed: list[str] = []

    # Check if both services already running
    server_running = is_service_running(SERVICES["debate-server"])
    web_running = is_service_running(SERVICES["debate-web"])

    if server_running and web_running:
        return MCPResponse(
            success=True,
            content=[
                MCPContent(
                    type=ContentType.JSON,
                    data={
                        "status": "already_running",
                        "services": {
                            "debate-server": {"port": 3456, "status": "running"},
                            "debate-web": {"port": 3457, "status": "running"},
                        },
                    },
                )
            ],
        )

    # Process each service that needs setup
    for name, service in SERVICES.items():
        # pnpm install if needed
        if _needs_install(service.cwd):
            steps_performed.append(f"pnpm install ({name})")
            success, error = _run_pnpm_install(service.cwd)
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
        if _needs_build(service):
            steps_performed.append(f"pnpm build ({name})")
            success, error = _run_pnpm_build(service)
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
        if not is_service_running(service) and not _check_pm2_process(name):
            needs_pm2_start = True
            break

    if needs_pm2_start:
        steps_performed.append("pm2 start")
        success, error = _start_services_with_pm2()
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
        success, error = _wait_for_service_healthy(service)
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
        content=[
            MCPContent(
                type=ContentType.JSON,
                data={
                    "status": "started",
                    "steps_performed": steps_performed,
                    "services": {
                        "debate-server": {"port": 3456, "status": "running"},
                        "debate-web": {"port": 3457, "status": "running"},
                    },
                },
            )
        ],
    )


def stop_services() -> MCPResponse:
    """Stop debate services via pm2."""
    try:
        result = subprocess.run(
            ["pm2", "stop", "debate-server", "debate-web"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # pm2 stop returns 0 even if process doesn't exist
        return MCPResponse(
            success=True,
            content=[
                MCPContent(
                    type=ContentType.JSON,
                    data={"status": "stopped", "output": result.stdout},
                )
            ],
        )
    except FileNotFoundError:
        return MCPResponse(
            success=False,
            error=MCPError(
                code="PM2_NOT_FOUND",
                message="pm2 not found",
                suggestion="Please install pm2: npm install -g pm2",
            ),
        )
    except Exception as e:
        return MCPResponse(
            success=False,
            error=MCPError(
                code="SERVICE_STOP_FAILED",
                message=str(e),
            ),
        )
