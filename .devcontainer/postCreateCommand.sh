#!/bin/bash

sudo apt-get update && sudo apt-get install -y libgraphviz-dev git-lfs

# Install dependencies except mlcroissant itself
pip install absl-py \
          datasets \
          etils[epath] \
          GitPython \
          jsonpath_rw \
          mypy \
          networkx \
          pandas \
          Pillow \
          pyarrow \
          pytest \
          pytype \
          rdflib \
          requests \
          torchdata \
          tqdm
