#!/bin/bash

sudo apt-get install -y libgraphviz-dev git-lfs

# Install dev packages.
pip3 install croissant/python/mlcroissant/.[devdeps]
