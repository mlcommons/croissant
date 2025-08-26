# Installation

This guide will help you install Eclair and get it running on your system. Eclair supports multiple installation methods depending on your needs.

## Quick Install

The fastest way to install Eclair is pip. Eclair works with **Python 3.10 or higher**.

```bash
pip install eclair
```

!!! note "Package Availability"
    The Eclair package will be published to PyPI soon. In the meantime, use the development installation method below.

## Development Installation

For the latest features or if you want to contribute to Eclair:

Clone the Repository

```bash
git clone https://github.com/mlcommons/croissant.git
cd eclair
```

Install Dependencies

```bash
pip install -r requirements.txt
```

Install in Development Mode

```bash
pip install -e .
```

Install Development Tools (Optional). For development with additional tools like testing and linting:

```bash
pip install -e .[dev]
```

You should now be able to run the Eclair server:

```bash
eclair-server
```

## Quick Start Script

Eclair includes a convenient setup script:

```bash
./start.sh
```

This script will:

- Install all required dependencies
- Set up the development environment  
- Start the Eclair server automatically


<img src="../../images/eclair-screen.png" alt="Eclair Diagram" style="max-width: 500px; height: auto;"/>


## Configuration

Eclair's behavior can be customized through configuration files and environment variables.

### Configuration File

Eclair uses `config.json` in the project root for its main configuration. This file controls server settings, upstream connections, and AI model preferences.

This is the default configuration.

```json
{
  "name": "Eclair Dataset MCP Server",
  "description": "MCP server to help AI models work with datasets, built on Croissant",
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "transport": "streamable-http"
  },
  "upstream_server": {
    "url": "https://mcp.jetty.io/mcp",
    "timeout": 5000
  },
  "gemini": {
    "model": "gemini-2.5-pro",
    "temperature": 0.3
  },
  "claude": {
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.3,
    "max_tokens": 4096
  }
}
```

### MCP Server settings

**Available Transport Methods:**

- `streamable-http` - HTTP streaming (recommended)
- `sse` - Server-sent events (deprecated)
- `stdio` - Standard input/output (for local usage)

### Upstream Server

Configuration for connecting to upstream MCP servers.

```json
{
  "upstream_server": {
    "url": "https://mcp.jetty.io/mcp",  // Upstream server URL
    "timeout": 5000,                    // Connection timeout (ms)
  }
}
```

!!! note "Compatible MCP servers"
    At the moment, Eclair has only been tested to work with Jetty.io, and is quite dependent on it. Over time, we hope to standardize the Eclair tools and allow multiple upstream MCP servers.


### AI Agent Configuration

Different AI agents require specific configuration:

#### Gemini CLI Configuration

Create `~/.gemini/settings.json`:
```json
{
  "mcpServers": {
    "eclair": {
      "httpUrl": "http://localhost:8080/mcp",
      "timeout": 5000
    }
  },
  "selectedAuthType": "gemini-api-key"
}
```

For step by step instructions, see the [Gemini CLI user guide](../usage/ai-agents/gemini-cli.md).

#### Claude Code Configuration

Register the server:
```bash
claude mcp add --transport http Eclair http://0.0.0.0:8080/mcp
```

For step by step instructions, see the [Claude Code user guide](../usage/ai-agents/claude-code.md).

#### VS Code MCP Configuration

Add to VS Code MCP settings:
```json
{
  "mcpServers": {
    "eclair": {
      "command": "eclair-server",
      "args": ["--transport", "stdio"]
    }
  }
}
```

For step by step instructions, see the [IDE user guide](../usage/ide/vscode-copilot.md).
