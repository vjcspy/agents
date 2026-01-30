"""Main entry point for the aw CLI."""

import typer

from aweave.core.node_loader import load_node_plugins
from aweave.core.python_loader import load_python_plugins

app = typer.Typer(
    name="aw",
    help="Unified CLI for development tools",
    no_args_is_help=True,
)


@app.command()
def version():
    """Show aw version."""
    from aweave import __version__

    typer.echo(f"aw version {__version__}")


# Load plugins
load_python_plugins(app)
load_node_plugins(app)


if __name__ == "__main__":
    app()
