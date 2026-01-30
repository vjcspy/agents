"""Load Python plugins via entry points."""

from importlib.metadata import entry_points

import typer


def load_python_plugins(app: typer.Typer) -> None:
    """Load Python plugins via entry points.

    Plugins register themselves using the 'dt.plugins' entry point group
    in their pyproject.toml:

        [project.entry-points."dt.plugins"]
        mycommand = "mypackage.cli:app"
    """
    try:
        eps = entry_points(group="dt.plugins")
    except TypeError:
        # Python < 3.10 compatibility
        eps = entry_points().get("dt.plugins", [])

    for ep in eps:
        try:
            plugin_app = ep.load()
            app.add_typer(plugin_app, name=ep.name)
        except Exception as e:
            typer.echo(
                f"Warning: Failed to load plugin '{ep.name}': {e}",
                err=True,
            )
