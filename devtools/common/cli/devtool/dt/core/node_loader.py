"""Load Node.js plugins via registry file and subprocess."""

import subprocess
from pathlib import Path

import typer
import yaml


def get_repo_root() -> Path:
    """Find repository root by walking up from this file."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        # Check for markers that indicate repo root
        if (parent / "dt-plugins.yaml").exists():
            return parent
        if (parent / "pyproject.toml").exists() and (parent / "pnpm-workspace.yaml").exists():
            return parent
    # Fallback: assume 5 levels up from this file
    return current.parents[4]


def get_registry_path() -> Path:
    """Get path to dt-plugins.yaml."""
    return get_repo_root() / "dt-plugins.yaml"


def load_node_plugins(app: typer.Typer) -> None:
    """Load Node plugins from registry and create subprocess wrappers.

    Node plugins are registered in dt-plugins.yaml with type: node.
    Each plugin is wrapped as a Typer command that delegates to the
    Node.js CLI via subprocess.
    """
    registry_path = get_registry_path()
    if not registry_path.exists():
        return

    try:
        with registry_path.open() as f:
            registry = yaml.safe_load(f)
    except Exception:
        return

    if not registry or "plugins" not in registry:
        return

    repo_root = registry_path.parent

    for name, config in registry.get("plugins", {}).items():
        if config.get("type") != "node":
            continue

        bin_path = repo_root / config["bin"]
        if not bin_path.exists():
            continue

        description = config.get("description", f"Node plugin: {name}")
        _create_node_wrapper(app, name, str(bin_path), description)


def _create_node_wrapper(
    app: typer.Typer,
    name: str,
    bin_path: str,
    description: str,
) -> None:
    """Create a Typer sub-app that wraps a Node.js CLI."""
    node_app = typer.Typer(
        help=description,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )

    # We need to capture bin_path in a closure
    def make_callback(bin_path: str):
        @node_app.callback(invoke_without_command=True)
        def wrapper(
            ctx: typer.Context,
        ):
            """Pass all arguments to the Node.js CLI."""
            if ctx.invoked_subcommand is not None:
                return

            cmd = ["node", bin_path, *ctx.args]

            try:
                result = subprocess.run(cmd)
                raise SystemExit(result.returncode)
            except FileNotFoundError as err:
                typer.echo("Error: Node.js not found. Please install Node.js.", err=True)
                raise SystemExit(1) from err

        return wrapper

    make_callback(bin_path)
    app.add_typer(node_app, name=name)
