"""Generates the virtual MkDocs docs tree from repository Markdown and images."""

from pathlib import Path

import mkdocs_gen_files

REPO_ROOT = Path(__file__).parent
GITHUB_TREE = "https://github.com/mlcommons/croissant/tree/main"
GITHUB_BLOB = "https://github.com/mlcommons/croissant/blob/main"
DOC_ASSET_EXTENSIONS = {".md", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".css"}


def _copy_doc(src_rel: str, dest_rel: str | None = None, rewrites=()) -> None:
    """Copy a text doc into the virtual MkDocs tree, applying link rewrites."""
    src = REPO_ROOT / src_rel
    if not src.exists():
        return
    content = src.read_text(encoding="utf-8")
    for old, new in rewrites:
        content = content.replace(old, new)
    with mkdocs_gen_files.open(dest_rel or src_rel, "w", encoding="utf-8") as dest:
        dest.write(content)


# 1. Root README -> index.md, plus repository-level Markdown docs.
_copy_doc(
    "README.md",
    "index.md",
    rewrites=(
        ("/docs/images/", "images/"),
        ("docs/images/", "images/"),
        ("](datasets/)", f"]({GITHUB_TREE}/datasets)"),
        (
            "](python/mlcroissant/recipes)",
            f"]({GITHUB_TREE}/python/mlcroissant/recipes)",
        ),
    ),
)
_copy_doc("CONTRIBUTING.md")
_copy_doc("LICENSE.md")

# 2. Subproject READMEs and docs (keeping source-code relative links valid).
_copy_doc(
    "python/mlcroissant/README.md",
    rewrites=(("(./mlcroissant/", f"({GITHUB_TREE}/python/mlcroissant/mlcroissant/"),),
)
_copy_doc("editor/README.md")
_copy_doc("health/README.md")
_copy_doc("health/croissant-validator-neurips/README.md")
_copy_doc("health/visualizer/explorer/README.md")
_copy_doc("croissant-rdf/README.md")
_copy_doc(
    "tasks/README.md",
    rewrites=(
        ("(croissant-tasks.ttl)", f"({GITHUB_BLOB}/tasks/croissant-tasks.ttl)"),
        (
            "(croissant-tasks-shapes.ttl)",
            f"({GITHUB_BLOB}/tasks/croissant-tasks-shapes.ttl)",
        ),
        ("(examples/)", f"({GITHUB_TREE}/tasks/examples)"),
        ("(docs/", "(tasks/docs/"),
    ),
)
_copy_doc(
    "tasks/docs/e3_croissant_tasks_integration.md",
    rewrites=(
        ("(../croissant-tasks.ttl)", f"({GITHUB_BLOB}/tasks/croissant-tasks.ttl)"),
        (
            "(../croissant-tasks-shapes.ttl)",
            f"({GITHUB_BLOB}/tasks/croissant-tasks-shapes.ttl)",
        ),
        ("(../examples/", f"({GITHUB_TREE}/tasks/examples/"),
    ),
)

# 3. Eclair documentation and images only (exclude Python code and caches).
_copy_doc("eclair/README.md")
for path in sorted((REPO_ROOT / "eclair" / "docs").rglob("*")):
    if path.is_file() and path.suffix.lower() in DOC_ASSET_EXTENSIONS:
        rel_path = path.relative_to(REPO_ROOT)
        with open(path, "rb") as src, mkdocs_gen_files.open(rel_path, "wb") as dest:
            dest.write(src.read())
