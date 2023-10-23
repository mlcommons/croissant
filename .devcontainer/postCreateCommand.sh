#!/bin/bash

sudo apt-get update
sudo apt-get install -y libgraphviz-dev

# Install dev packages.
pip3 install python/mlcroissant/.[dev]

# Install library stubs for mypy checks.
sudo mypy --install-types