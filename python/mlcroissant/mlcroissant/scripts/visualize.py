"""Visualizes a Croissant dataset as an interactive HTML page.

This script:

  1. Augments the raw Croissant JSON-LD with ``cr:examples`` preview data
     (file listings for FileSets, sample rows for RecordSets).
  2. Writes a minimal HTML shell that embeds the augmented JSON-LD as
     ``window.__CROISSANT_DATA__`` for the client-side renderer.
  3. Copies ``static/visualizer.js`` and ``static/visualizer.css`` next to
     the output HTML file so the page can load them with relative paths.

Usage (standalone)::

    python -m mlcroissant.scripts.visualize \
        --jsonld datasets/1.0/titanic/metadata.json \
        --output datasets/1.0/titanic/index.html
"""

from etils import epath

from mlcroissant.scripts.visualize_utils import visualize_js


def main(argv: list | None = None) -> None:
    """Entry point when run as a standalone script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a JS-driven Croissant visualizer HTML page."
    )
    parser.add_argument(
        "--jsonld", required=True, help="Path to the Croissant JSON-LD file."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output HTML file (default: index.html next to the JSON-LD).",
    )
    parser.add_argument(
        "--static_path",
        default=".",
        help="Path or URL to the js and css directory (default: .).",
    )
    args = parser.parse_args(argv)
    jsonld = args.jsonld
    if args.output:
        output = epath.Path(args.output)
    else:
        output = epath.Path(jsonld).parent / "index.html"
    visualize_js(jsonld=jsonld, output=output, static_path=args.static_path)


if __name__ == "__main__":
    main()
