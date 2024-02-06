#!/bin/bash

apt-get update && apt-get install -y libgraphviz-dev

# Install dev packages.
pip3 install croissant/python/mlcroissant/.[dev_deps]
