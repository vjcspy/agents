"""Main entry point for the dt CLI."""

import typer

from dt.core.node_loader import load_node_plugins
from dt.core.python_loader import load_python_plugins

app = typer.Typer(
    name="dt",
    help="Unified CLI for development tools",
    no_args_is_help=True,
)


@app.command()
def version():
    """Show dt version."""
    from dt import __version__

    typer.echo(f"dt version {__version__}")


# Load plugins
load_python_plugins(app)
load_node_plugins(app)


if __name__ == "__main__":
    app()
