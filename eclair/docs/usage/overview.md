# Usage Overview

Eclair is designed to be flexible and accessible through multiple interfaces, each suited for different workflows and use cases. This section covers all the ways you can use Eclair to discover, analyze, and work with datasets. 

Below are usage guides for an initial set of AI agents and interfaces, but in principle any agent that supports MCP can leverage Eclair. Feel free to update this documentation with additional guides!

## 🤖 AI Agents with CLI

- **[Gemini CLI](ai-agents/gemini-cli.md)** - Command-line AI assistant powered by Google's Gemini models
- **[Claude Code](ai-agents/claude-code.md)** - Command-line AI assistant powered by Anthropic's Claude models

## 🔧 IDE Integration

Seamless integration into your development environment:

- **[VS Code + Copilot](ide/vscode-copilot.md)** - GitHub Copilot enhanced with Eclair 
- **[VS Code + Gemini Code Assist](ide/vscode-gemini.md)** - Google's Gemini Code Assist enhanced with Eclair's capabilities

Of course, you can also use Eclair with other IDEs such as Cursor.

## 🐍 Python API

Programmatic access for automation and integration:

- **[Python API](python-api.md)** - Provides access to all Eclair tools via a Python API
- Three client types: `EclairClient` (base MCP), `GeminiMCPClient` (AI-powered), `ClaudeMCPClient` (AI-powered)
- Perfect for Jupyter notebooks, data pipelines, and automated workflows

## ⚡ Command Line Interface

Quick dataset operations from the terminal:

- **[CLI Reference](cli.md)** - Complete command-line interface to all Eclair tools
- Also supports AI-powered commands (in natural language) as in the Python API
- Ideal for scripting, automation, and quick dataset queries