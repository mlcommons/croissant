# Running the Server

Once you have Eclair installed, you need to run the server to enable AI agents to access datasets. This guide covers different ways to start and manage the Eclair server.

## Quick Start

The simplest way to run Eclair:

```bash
eclair-server
```

This starts the server with default settings:

- **Host**: 0.0.0.0 (accessible from any network interface)
- **Port**: 8080
- **Transport**: streamable-http

You should see output similar to:
```
⚡️ Starting Eclair Server...
🌐 Server running at http://0.0.0.0:8080/mcp
🔧 Transport: streamable-http
✅ Server ready for connections!
```

## Command Line Options

Customize the server with command-line arguments:

```bash
eclair-server --host 127.0.0.1 --port 9000 --transport sse
```

### Available Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--host` | `-h` | Host to bind to | `0.0.0.0` |
| `--port` | `-p` | Port to listen on | `8080` |
| `--transport` | `-t` | Transport method | `streamable-http` |
| `--config` | `-c` | Config file path | `config.json` |
| `--verbose` | `-v` | Enable verbose logging | `False` |
| `--help` |  | Show help message |  |

## Manual Server Execution

You can also run the server directly from the Python module:

```bash
python server/server.py --host 0.0.0.0 --port 8080 --transport streamable-http
```

Or from within the source directory:
```bash  
cd /path/to/eclair
python -m src.eclair.server.server
```

## Configuration-Based Startup

For consistent deployments, use a configuration file:

```bash
eclair-server --config /path/to/config.json
```

The server will read all settings from the config file. See [Configuration](installation.md) for details.

## Process Management

### Running in Background

**On macOS/Linux:**
```bash
# Start in background
nohup eclair-server > eclair.log 2>&1 &

# Check if running
ps aux | grep eclair-server

# Stop server
pkill -f eclair-server
```

### Common Error Messages

**"Address already in use"**

- Port 8080 is busy, maybe by another Eclair server. Use `--port` to specify a different port or shut down the other service on port 8080.

**"Connection refused"**

- Check firewall settings
- Verify server is running
- Confirm correct host/port