# Generates MkDocs pages from various parts of the repo.
# MKDocs expects all documentation files to be in the 'docs/' directory.
# This script this called when building mkdocs to copy documentation from 
# other parts of the repo to a virtual 'docs/' directory.
from pathlib import Path

import mkdocs_gen_files

# Get the root directory of the repo
root = Path(__file__).parent

# 1. Copy the Root README to 'index.md' AND fix image paths
with open(root / "README.md", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("/docs/images/", "images/")
content = content.replace("docs/images/", "images/")

with mkdocs_gen_files.open("index.md", "w", encoding="utf-8") as dest:
    dest.write(content)

# 2. List of folders you want to include from the root
folders_to_include = ["python", "eclair", "editor", "health", "croissant-rdf"]

for folder in folders_to_include:
    # Recursively copy all files from these folders
    for path in sorted((root / folder).rglob("*")):
        if path.is_file():
            # Calculate the relative path (e.g., python/mlcroissant/README.md)
            rel_path = path.relative_to(root)
            # Write it to the virtual docs directory
            with open(path, "rb") as src:
                with mkdocs_gen_files.open(rel_path, "wb") as dest:
                    dest.write(src.read())