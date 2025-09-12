"""
CLI entry point for Eclair client
"""
import argparse
import asyncio
import json

from .client import EclairClient
from .gemini import GEMINI_AVAILABLE
from .gemini import GeminiMCPClient

try:
    from .claude import CLAUDE_AVAILABLE
    from .claude import ClaudeMCPClient
except ImportError:
    ClaudeMCPClient = None
    CLAUDE_AVAILABLE = False


async def async_main():
    """Async CLI entry point for the Eclair client."""
    parser = argparse.ArgumentParser(description="Eclair MCP Client")
    parser.add_argument("--server-url", "-S", default="http://localhost:8080/mcp", help="MCP server URL")
    parser.add_argument("--tool", "-T", required=True, help="Tool to call")
    parser.add_argument("--query", "-Q", help="Query string for search-datasets")
    parser.add_argument("--collection", "-C", help="Dataset collection")
    parser.add_argument("--dataset", "-D", help="Dataset name")
    parser.add_argument("--use-gemini", "-G", action="store_true", help="Use Gemini client")
    parser.add_argument("--use-claude", "-L", action="store_true", help="Use Claude client")
    args = parser.parse_args()
    
    # Check for mutually exclusive options
    if args.use_gemini and args.use_claude:
        print("Error: Cannot use both --use-gemini and --use-claude at the same time")
        return
    
    if args.use_gemini:
        if not GEMINI_AVAILABLE:
            print("Error: Gemini not available. Install with: pip install google-generativeai")
            return
        client = GeminiMCPClient(args.server_url)
        await client.initialize()
        
        if args.tool == "ask":
            if not args.query:
                print("Error: --query required for ask command")
                return
            response = await client.ask_gemini_with_tools(args.query)
            print(response)
        else:
            # Call MCP tool directly
            if args.tool == "search-datasets" and args.query:
                result = await client.search_datasets(args.query)
            else:
                arguments = {}
                if args.query:
                    arguments["query"] = args.query
                if args.collection:
                    arguments["collection"] = args.collection
                if args.dataset:
                    arguments["dataset"] = args.dataset
                
                result = await client.call_mcp_tool(args.tool, arguments)
                print(result)
            
    elif args.use_claude:
        if not CLAUDE_AVAILABLE:
            print("Error: Claude not available. Install with: pip install anthropic")
            return
        client = ClaudeMCPClient(args.server_url)
        await client.initialize()
        
        if args.tool == "ask":
            if not args.query:
                print("Error: --query required for ask command")
                return
            response = await client.ask_claude_with_tools(args.query)
            print(response)
        else:
            # Call MCP tool directly
            arguments = {}
            if args.query:
                arguments["query"] = args.query
            if args.collection:
                arguments["collection"] = args.collection
            if args.dataset:
                arguments["dataset"] = args.dataset
            
            result = await client.search_datasets(args.query) if args.tool == "search-datasets" and args.query else None
            if result:
                print(result)
            else:
                print(f"Tool '{args.tool}' not implemented for Claude client yet")
    else:
        client = EclairClient(args.server_url)
        await client.initialize()
        
        # Map tool names to methods
        tool_methods = {
            "ping": client.ping,
            "help": client.get_help,
            "search-datasets": lambda: client.search_datasets(args.query) if args.query else print("Error: --query required"),
            "download-dataset": lambda: client.download_dataset(args.collection, args.dataset) if args.collection and args.dataset else print("Error: --collection and --dataset required"),
            "datasets-preview-url": lambda: client.datasets_preview_url(args.collection, args.dataset) if args.collection and args.dataset else print("Error: --collection and --dataset required"),
            "serve-croissant": lambda: client.serve_croissant(args.collection, args.dataset) if args.collection and args.dataset else print("Error: --collection and --dataset required"),
        }
        pretty_print = ["search-datasets", "download-dataset", "datasets-preview-url", "serve-croissant"]
        
        if args.tool in tool_methods:
            result = await tool_methods[args.tool]()
            if result:
                if args.tool in pretty_print:
                    # Pretty print JSON with proper indentation
                    json_data = result.structured_content['result']
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                else:
                    print(result)
        else:
            print(f"Unknown tool: {args.tool}")
            print(f"Available tools: {list(tool_methods.keys())}")


def main():
    """Synchronous entry point that runs the async main function."""
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
