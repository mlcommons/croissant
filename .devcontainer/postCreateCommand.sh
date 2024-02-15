#!/bin/bash

sudo apt-get update && sudo apt-get install -y graphviz libgraphviz-dev git-lfs

# Install dependencies except mlcroissant itself
cd /workspaces/croissant/python/mlcroissant
pip install -e .[dev]
