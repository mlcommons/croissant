"""Main entry point for mlcroissant CLI."""

import importlib
import sys

from absl import app


class Commands:
    """Possible commands."""

    DOCUMENTATION = "documentation"
    LOAD = "load"
    VALIDATE = "validate"


choices = set([
    Commands.DOCUMENTATION,
    Commands.LOAD,
    Commands.VALIDATE,
])


def main():
    """Main function for the CLI."""
    if len(sys.argv) < 2:
        raise ValueError(f"usage: mlcroissant {choices}")
    choice = sys.argv[1]
    if choice not in choices:
        raise ValueError(f"usage: mlcroissant {choices}. Got: `mlcroissant {choice}`")
    module = importlib.import_module(f"mlcroissant.scripts.{choice}")
    app.run(module.main)
