#!/bin/bash

# Eclair dataset server quickstart script for development
set -e

# Install in development mode if not already installed
if ! command -v eclair-server &> /dev/null; then
    echo "Installing Eclair in development mode..."
    pip install -e .
fi

# Start the server
eclair-server --host 0.0.0.0 --port 8080 --transport streamable-http
