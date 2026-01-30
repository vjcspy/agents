"""Load Python plugins via entry points."""

from importlib.metadata import entry_points

import typer


def load_python_plugins(app: typer.Typer) -> None:
    """Load Python plugins via entry points.

    Plugins register themselves using the 'aw.plugins' entry point group
    in their pyproject.toml:

        [project.entry-points."aw.plugins"]
        mycommand = "mypackage.cli:app"
    """
    try:
        eps = entry_points(group="aw.plugins")
    except TypeError:
        # Python < 3.10 compatibility
        eps = entry_points().get("aw.plugins", [])

    for ep in eps:
        try:
            plugin_app = ep.load()
            app.add_typer(plugin_app, name=ep.name)
        except Exception as e:
            typer.echo(
                f"Warning: Failed to load plugin '{ep.name}': {e}",
                err=True,
            )
