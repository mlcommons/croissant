"""
Gemini MCP Client

Client that connects Gemini to the Eclair MCP Server.
"""
import json
import os
from typing import Optional
import warnings

# Suppress known protobuf enum warnings from Google AI library
warnings.filterwarnings("ignore", message="Unrecognized FinishReason enum value", category=UserWarning)
# Suppress protobuf deprecation warning for including_default_value_fields
warnings.filterwarnings("ignore", message=".*including_default_value_fields.*", category=DeprecationWarning)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from fastmcp import Client

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, will use system environment variables only
    pass

class GeminiMCPClient:
    """Client that connects Gemini to the Eclair MCP Server."""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8080/mcp", gemini_api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai is not installed. Install it with: pip install google-generativeai")
            
        self.mcp_server_url = mcp_server_url
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.mcp_client = None
        self.gemini_client = None
        
        # Load configuration from config.json
        self._load_config()
        
        # Load system prompt from gemini.md
        self._load_system_prompt()
        
    def _load_config(self):
        """Load configuration from config.json file."""
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "config.json")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            gemini_config = config.get('gemini', {})
            self.model_name = gemini_config.get('model', 'gemini-2.0-flash-exp')
            self.default_temperature = gemini_config.get('temperature', 0.3)
            
        except Exception as e:
            print(f"Warning: Could not load config.json: {e}")
            # Use defaults
            self.model_name = "gemini-2.0-flash-exp"
            self.default_temperature = 0.3
    
    def _load_system_prompt(self):
        """Load system prompt from gemini.md file."""
        system_prompt_path = os.path.join(os.path.dirname(__file__), "gemini.md")
        try:
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract the main prompt content, removing markdown headers
            # Keep the core instructions but clean up formatting
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                # Skip markdown headers but keep the content
                if line.startswith('#'):
                    continue
                cleaned_lines.append(line)
            
            self.system_prompt = '\n'.join(cleaned_lines).strip()
            return True
            
        except Exception as e:
            print(f"Warning: Could not load system prompt from gemini.md: {e}")
            # Use a basic fallback prompt
            self.system_prompt = """You are a helpful data scientist AI assistant. You have access to MCP tools for finding and analyzing datasets. Always try to use the available tools to search for and analyze real data to answer user questions."""
            return False
        
    async def initialize(self):
        """Initialize both MCP and Gemini clients."""
        # Initialize MCP client to connect to our Eclair server
        self.mcp_client = Client(self.mcp_server_url)
        
        # Initialize Gemini client if API key is available
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_client = genai  # Use the configured module
            # print(f"Gemini API configured with key: {self.gemini_api_key[:10]}...")
        else:
            print("No Gemini API key found. Only MCP functionality will be available.")
    
    async def close(self):
        """Clean up resources."""
        # The MCP client will be closed automatically when exiting the context manager
        # Gemini client doesn't need explicit cleanup
        pass

    async def ask_gemini_with_tools(self, prompt: str, temperature: Optional[float] = None):
        """Use Gemini with MCP tools and system prompt."""
        if not self.gemini_client:
            raise ValueError("Gemini client not available (no API key)")
        
        # Use provided temperature or default from config
        temp = temperature if temperature is not None else self.default_temperature
            
        async with self.mcp_client:
            try:
                print("Thinking...")
                # Create the full conversation with system prompt embedded in user message
                full_prompt = f"""{self.system_prompt}

---

User Request: {prompt}

Available MCP Tools:
- search-datasets: Search for datasets using a query string
- serve-croissant: Get Croissant metadata for a dataset
- download-dataset: Download dataset files
- datasets-preview-url: Get preview URLs for datasets
- validate-croissant: Validate Croissant metadata

Instructions: Follow your data scientist workflow by searching for relevant datasets and analyzing their metadata based on the user's request. 
If you need to use tools, also execute them."""

                # Use Gemini to generate a response
                model = genai.GenerativeModel(self.model_name)
                
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(temperature=temp)
                )
                
                return response.text
                
            except Exception as e:
                # Fallback: try a simpler approach with basic dataset search
                try:
                    # Extract search terms from the user prompt
                    search_terms = self._extract_search_terms(prompt)
                    if search_terms:
                        search_result = await self.mcp_client.call_tool("search-datasets", {"query": search_terms})
                        
                        enhanced_prompt = f"""As a data scientist AI assistant, I searched for datasets related to '{search_terms}' based on your request: "{prompt}"

I found these datasets:
{search_result}

Let me analyze these results and provide recommendations."""
                        
                        model = genai.GenerativeModel(self.model_name)
                        response = model.generate_content(
                            enhanced_prompt,
                            generation_config=genai.types.GenerationConfig(temperature=temp)
                        )
                        return response.text
                        
                except Exception as fallback_error:
                    # Final fallback
                    model = genai.GenerativeModel(self.model_name)
                    response = model.generate_content(
                        f"I apologize, but I'm having trouble accessing the dataset server right now. However, I can provide general guidance about: {prompt}",
                        generation_config=genai.types.GenerationConfig(temperature=temp)
                    )
                    return f"⚠️ Dataset server unavailable. General guidance:\n\n{response}"
    
    def _extract_search_terms(self, prompt: str) -> str:
        """Extract relevant search terms from user prompt."""
        # Enhanced search term extraction based on the sophisticated system prompt
        prompt_lower = prompt.lower()
        
        # Look for specific domain keywords
        if any(keyword in prompt_lower for keyword in ["image", "classification", "computer vision", "cv"]):
            if "animal" in prompt_lower or "cat" in prompt_lower or "dog" in prompt_lower:
                return "image classification animals"
            elif "medical" in prompt_lower:
                return "medical image classification"
            else:
                return "image classification"
        elif any(keyword in prompt_lower for keyword in ["medical", "health", "disease", "clinical"]):
            return "medical health"
        elif any(keyword in prompt_lower for keyword in ["mnist", "digit", "handwritten"]):
            return "mnist handwritten digits"
        elif any(keyword in prompt_lower for keyword in ["nlp", "language", "text", "sentiment"]):
            return "natural language processing text"
        elif any(keyword in prompt_lower for keyword in ["climate", "weather", "temperature"]):
            return "climate weather data"
        else:
            # Extract meaningful words
            words = prompt_lower.split()
            meaningful_words = [w for w in words if len(w) > 3 and w not in [
                "find", "search", "datasets", "about", "with", "that", "have", "need", "want", "looking"
            ]]
            return " ".join(meaningful_words[:3]) if meaningful_words else "data"

    async def search_datasets(self, query: str) -> dict:
        """Search for datasets using the MCP server."""
        async with self.mcp_client:
            print(f"Searching for datasets on {query}")
            final_results = {"I": "Am a atest"}

            if self.gemini_client:
                try:
                    model = self.gemini_client.GenerativeModel(self.model_name)
                    # generate_content is synchronous in google-generativeai
                    gemini_search_results = model.generate_content(f"Find datasets that have a valid croissant file about this topic : {query}")
                    formatted_gemini_search_results = (getattr(gemini_search_results, 'text', None) or "").strip()
                    print(f"Found datasets from gemini {formatted_gemini_search_results}")
                    logger.info(f"Found datasets from gemini {formatted_gemini_search_results}")
                    main_search_results = await self.mcp_client.call_tool("search-datasets", {"query": query})

                    combined = model.generate_content(
                        f"Combine the results into the same format as main_search_results : {main_search_results} along with {formatted_gemini_search_results}"
                    )
                    final_results = (getattr(combined, 'text', None) or "").strip() or combined
                    logger.info(f"Final results {final_results}")
                except Exception as e:
                    logger.info(f"Exception {e}")
                    final_results = await self.mcp_client.call_tool("search-datasets", {"query": query})

            return final_results

    async def serve_croissant(self, collection: str, dataset: str) -> dict:
        """Get Croissant metadata for a specific dataset."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("serve-croissant", {
                "collection": collection,
                "dataset": dataset
            })

    async def download_dataset(self, collection: str, dataset: str) -> dict:
        """Download a dataset."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("download-dataset", {
                "collection": collection,
                "dataset": dataset
            })

    async def datasets_preview_url(self, collection: str, dataset: str) -> dict:
        """Get preview URL for a dataset."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("datasets-preview-url", {
                "collection": collection,
                "dataset": dataset
            })

    async def call_mcp_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Generic method to call any MCP tool."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool(tool_name, arguments or {})

    async def ping(self) -> dict:
        """Ping the MCP server."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("ping")

    async def get_help(self) -> dict:
        """Get help information from the MCP server."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("help")

    async def validate_croissant(self, metadata_json: dict) -> dict:
        """Validate Croissant metadata."""
        async with self.mcp_client:
            return await self.mcp_client.call_tool("validate-croissant", {"metadata_json": metadata_json})


# Example usage (only if running this file directly)
if __name__ == "__main__":
    import asyncio
    
    async def main():
        client = GeminiMCPClient()
        await client.initialize()
        
        # Example: Search for datasets
        print("Searching for image datasets...")
        results = await client.search_datasets("image classification")
        print(f"Found datasets: {results}")
        
        await client.close()
    
    asyncio.run(main())
