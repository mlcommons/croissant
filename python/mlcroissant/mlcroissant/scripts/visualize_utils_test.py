"""Tests for visualizer static asset emission and HTML generation."""

import builtins
import pathlib
import sys

from mlcroissant._src.core import constants
from mlcroissant.scripts import cli
from mlcroissant.scripts import visualize_utils


def test_visualize_js_standalone_writes_minified_assets(tmp_path: pathlib.Path):
    """Standalone output creates missing parent dirs and emits .min.* assets."""
    jsonld = constants.DATASETS_FOLDER / "1.0" / "titanic" / "metadata.json"
    output = tmp_path / "nested" / "sub" / "index.html"

    visualize_utils.visualize_js(jsonld=jsonld, output=output)

    assert output.exists()
    html = output.read_text(encoding="utf-8")
    assert "window.__CROISSANT_DATA__" in html
    assert "window.__GALLERY_URL__" not in html
    assert "./visualizer.min.css" in html
    assert "./visualizer.min.js" in html
    assert (output.parent / "visualizer.min.css").exists()
    assert (output.parent / "visualizer.min.js").exists()


def test_visualize_js_standalone_falls_back_without_minifiers(
    tmp_path: pathlib.Path, monkeypatch
):
    """Asset emission falls back to copying raw files without dev minifiers."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"jsmin", "csscompressor"}:
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    jsonld = constants.DATASETS_FOLDER / "1.0" / "titanic" / "metadata.json"
    output = tmp_path / "fallback" / "index.html"

    visualize_utils.visualize_js(jsonld=jsonld, output=output)

    assert (output.parent / "visualizer.min.css").read_text(encoding="utf-8") == (
        visualize_utils._STATIC_DIR / "visualizer.css"
    ).read_text(encoding="utf-8")
    assert (output.parent / "visualizer.min.js").read_text(encoding="utf-8") == (
        visualize_utils._STATIC_DIR / "visualizer.js"
    ).read_text(encoding="utf-8")


def test_visualize_js_with_shared_static_path_skips_copy(tmp_path: pathlib.Path):
    """Gallery mode injects back-link and does not duplicate static assets."""
    jsonld = constants.DATASETS_FOLDER / "1.0" / "titanic" / "metadata.json"
    output = tmp_path / "gallery_item" / "index.html"

    visualize_utils.visualize_js(
        jsonld=jsonld,
        output=output,
        static_path="../../static",
        gallery_url="../../index.html",
    )

    html = output.read_text(encoding="utf-8")
    assert 'window.__GALLERY_URL__="../../index.html"' in html
    assert "../../static/visualizer.min.css" in html
    assert not (output.parent / "visualizer.min.css").exists()
    assert not (output.parent / "visualizer.min.js").exists()


def test_cli_visualize_entrypoint(tmp_path: pathlib.Path, monkeypatch):
    """The `mlcroissant visualize` CLI entrypoint forwards flags to argparse."""
    jsonld = constants.DATASETS_FOLDER / "1.0" / "titanic" / "metadata.json"
    output = tmp_path / "cli_out" / "index.html"
    monkeypatch.setattr(
        sys,
        "argv",
        ["mlcroissant", "visualize", "--jsonld", str(jsonld), "--output", str(output)],
    )

    cli.main()

    assert output.exists()
    assert (output.parent / "visualizer.min.css").exists()
    assert (output.parent / "visualizer.min.js").exists()
