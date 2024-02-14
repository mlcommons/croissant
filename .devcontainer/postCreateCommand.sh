#!/bin/bash

sudo apt-get update && sudo apt-get install -y libgraphviz-dev git-lfs

# Install dependencies except mlcroissant itself
cd ../python/mlcroissant
pip install -e ../python/mlcroissant/.[dev]
