"""Main entry point for mlcroissant CLI."""

import importlib
import sys

from absl import app


class Commands:
    """Possible commands."""

    FROM_HUGGINGFACE_TO_CROISSANT = "from_huggingface_to_croissant"
    LOAD = "load"
    VALIDATE = "validate"


choices = set([
    Commands.FROM_HUGGINGFACE_TO_CROISSANT,
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
    if choice == Commands.FROM_HUGGINGFACE_TO_CROISSANT:
        raise ValueError(
            "This conversion script is deprecated. Please, use Hugging Face's API"
            " endpoint:"
            " https://datasets-server.huggingface.co/croissant?dataset={dataset} where"
            " `dataset` is the ID the dataset on Hugging Face Hub."
        )
    module = importlib.import_module(f"mlcroissant.scripts.{choice}")
    app.run(module.main)
