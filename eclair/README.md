
<div align="center">
<h1 style="border-bottom: none; text-decoration: none;">⚡️ Eclair ⚡️</h1>
</div>

# Your lightning-fast data scientist

Eclair is a set of agentic tools that helps AI models (like Gemini and Claude) discover, download, and use datasets to answer questions based on factual data. Today, such models struggle to discover and use structured data to answer questions, which limits their scientific and analytical potential.

With Eclair, AI models can answer your questions by easily accessing millions of datasets available all over the world, and analysing this data to give accurate answers, rather than having to guess based on training data or web searches. It's like having your own personal, lightning-fast data scientist.

<img src="docs/images/eclair-diagram.png" alt="Eclair Diagram"/>

Eclair does this by combining three recent technologies:
* The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/getting-started/intro) to give AI models easy access to millions of datasets available online (or your own), and tools to work effectively with that data.
* The [Croissant](https://github.com/mlcommons/croissant) metadata standard to help AI models understand what information each dataset contains and how to download and extract that information.
* [AI assistants](https://modelcontextprotocol.io/clients) that can 'think' about how to answer your questions, find relevant datasets, write code to download and analyze this data, and generate anything from direct textual answers to detailed notebooks, voice summaries, and custom user interfaces.

Most importantly, Eclair aims to create an **open, global ecosystem** of data sources, agentic tools, and other MCP servers that can be accessed by any AI agent and extended by anyone. You can also run Eclair servers locally, connect it to your own data sources, extend them with more advanced data analysis tools, actively generate data on the fly, or practically anything that you can imagine.

<table>
<tr>
<td><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Eclairs_with_chocolate_icing_at_Cafe_Blue_Hills.jpg/960px-Eclairs_with_chocolate_icing_at_Cafe_Blue_Hills.jpg?uselang=fr" width=200/></td>
<td>Fun fact: like 🥐 Croissant, Éclair was born in Paris. It's both a delicious pastry and the French word for ⚡️ lightning ⚡️.</td>
</tr>
</table>

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [Using Eclair](#using-eclair)
  - [Gemini CLI](#gemini-cli)
  - [Claude Code](#claude-code)
  - [IDE integration](#ide-integration)
    - [With VSCode and Copilot](#with-vscode-and-copilot)
    - [With VSCode and Google Code Assist](#with-vscode-and-google-code-assist)
  - [Python API](#python-api)
    - [Basic Usage](#basic-usage)
    - [Using AI models](#using-ai-models)
  - [Command Line Interface](#command-line-interface)
- [Development](#development-1)

## Features

- **Built on Croissant**: A widely accepted machine-readable metadata format for datasets
- **FastMCP Implementation**: Built using the latest FastMCP library and MCP SDK.
- **Seemlessly integrates** with developer environments (e.g. VSCode), code assistants (e.g. Copilot and Gemini Code Assist) and command-line or desktop AI agents.
- **Portable**: Easy to set up your own server and interact via Python code or command-line commands.
- **Flexible Design**: Can relay to other MCP servers (e.g. [Jetty](https://jetty.io/)) and run anywhere as a stateless server.

### Currently Available Tools

1. **search-datasets**: Search for datasets using a query string
2. **download-dataset**: Download a dataset with metadata
3. **datasets-preview-url**: Get a download URL for a dataset preview
4. **serve-croissant**: Get the Croissant metadata for a given dataset
5. **validate-croissant**: Validate a Croissant metadata file
6. **help**: Get instructions to use the Eclair tools
7. **ping**: Test that your Eclair server is working


## Installation

You can install Eclair with:

```bash
pip install eclair
```
*Note: Package will be published to PyPI soon*

### Development
Install the required dependencies in a Python environment:
```bash
pip install -r requirements.txt
```

Install in development mode:
```bash
pip install -e .
```

For development with additional tools:
```bash
pip install -e .[dev]
```

Alternatively, use the provided quickstart script to install and start the server:
```bash
./start.sh
```

# Running the Server

## Using the Package (Recommended)
If you've installed the package, simply run
```sh
eclair-server
```

Or if you want to specify host, port, and transport:

```sh
eclair-server --host 0.0.0.0 --port 8080 --transport streamable-http
```

Command line arguments:

- `--host`: Host to bind to (default: 0.0.0.0, configured in config.json)
- `--port`: Port to listen on (default: 8080, configured in config.json)  
- `--transport`: Transport method - 'streamable-http', 'sse', or 'stdio' (default: streamable-http)

## Run manually
The main server file is `server/server.py`. You can run it manually with the same configuration options:

```sh
python server/server.py --host 0.0.0.0 --port 8080 --transport streamable-http
```

## Configuration

### Server configuration
You can configure the server in the `config.json` file. This includes upstream MCP servers (currently only one), and model versions preferences. 

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

# Using Eclair

✨ Eclair can be used by a wide variety of AI agents (any agent that understands MCP), 
such as **Gemini CLI, Claude Code, and IDE integrations such as Gemini Code Assist and Copilot**.

👩‍💻 Moreover, we provide a **Python package** to use Eclair in Jupyter notebooks, Google Colab, and your own code, as well as a **CLI** for quick interactions and further integration.


## Gemini CLI
Install [Gemini CLI](https://github.com/google-gemini/gemini-cli) (and [node.js](http://node.js)).

```bash
npm install -g @google/gemini-cli
```

Set your Gemini API key in an .env file
```bash
echo "GEMINI_API_KEY=XXX" >> .env
```

Add the MCP server in `~/.gemini/settings.json` (in your home dir)
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

Copy the system prompt to your local working directory.
```bash
cp src/eclair/client/gemini/gemini.md ./GEMINI.md
```

Make sure that your Eclair server is running (see above), then start Gemini CLI
```bash
gemini
```

Check that you see the red sunglasses (this means that the system prompt is loaded) and `Using: 1 MCP server`

<img src="docs/images/gemini.png" alt="Gemini CLI"/>

Type `\mcp` in the prompt to make sure all the Eclair tools are accessible.


### Example
Let's use Eclair to explore some fashion-related datasets.

<details>
<summary>Click to expand the Gemini CLI example</summary>

```bash
Prompt: Find a fashion-related dataset and visualize some data examples
```

* First, Gemini uses Eclair to find relevant datasets. 
* It prompts you when it needs permissions (e.g. to run tools or execute code)

<img src="docs/images/fashion-1.png" alt="Fashion query"/>

* Eclair will return all relevant datasets with metadata.
* Gemini may make a recommendation and elicit your preference.

<img src="docs/images/fashion-2.png" alt="Fashion select"/> 

* Next, Gemini downloads the dataset using metadata and download instructions provided by Eclair (in JSON).

<img src="docs/images/fashion-3.png" alt="Fashion download"/> 

* Next, Gemini generates and runs the full code to answer the question.

<img src="docs/images/fashion-4.png" alt="Fashion code"/> 

* Succes! 

<img src="docs/images/fashion_mnist_examples.png" alt="Eclair Diagram" width=400/>

* Of course, you can keep interacting with Gemini to work with the data. For instance:

```
> What is a good model to predict the type of clothing? Evaluate a few of them.
```

<details>
<summary>Click to expand the full conversation and generated code</summary>

<img src="docs/images/fashion-5a.png" alt="Fashion code"/> 
<img src="docs/images/fashion-5b.png" alt="Fashion code"/>
</details>


<img src="docs/images/fashion-5.png" alt="Fashion code"/> 
</details>

## Claude Code
Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

If you are new to Claude Code, run `claude` and follow the prompts to link it to your account. Then exit (Ctrl-C).

```bash
claude
```

Register the Eclair MCP server

```bash
claude mcp add --transport http Eclair http://0.0.0.0:8080/mcp
```

Copy the Eclair system prompt to your local working directory.
```bash
cp src/eclair/client/claude/claude.md ./CLAUDE.md
```

Make sure that your Eclair server is running, then start Claude

```bash
claude
```

You can check whether Eclair is connected by running `eclair ping`
<img src="docs/images/claude.png" alt="Claude code"/> 



### Example
Let's try running the same query as above.

<details>
<summary>Click to expand the Claude Code example</summary>

```
> Find a fashion-related dataset and visualize some data examples
```
Claude decides to use the Eclair tools and prompts you when it needs permissions.
<img src="docs/images/claude-1.png" alt="Fashion query"/>

You select which dataset you want to use, then Claude uses Eclair to download that dataset.
<img src="docs/images/claude-2.png" alt="Fashion select"/>

Next, Claude writes code to visualize the dataset
<img src="docs/images/claude-3.png" alt="Fashion visualize"/>
<img src="docs/images/claude-4.png" alt="Fashion visualize"/>
<img src="docs/images/claude-6.png" alt="Fashion visualize"/>

Finally, like a good data scientist, Claude generates a report about what was learned so far. 
<img src="docs/images/claude-5.png" alt="Fashion summary"/>

</details>

## IDE integration
IDE's are a great environment to interactively explore datasets using Eclair and AI models. There are a tremendous amount of tools available to do this. We'll focus on VSCode together with Copilot and Gemini Code Assist, but other tools will work very similarly.

### With VSCode and Copilot
First, we need to register Eclair:
* In the VSCode search bar, enter ‘>mcp’
* Choose ‘MCP: Add Server’
* Type: choose HTTP
* URL: enter ‘http://0.0.0.0:8080/mcp’ to use your local server
* ID: “Eclair”
* Choose Global or Workspace
* The mcp.json file may open to confirm

Under Extensions (left bar 'box' icon), scroll down to MCP servers to find Eclair, then click the gear icon to 'Start Server'.
<img src="docs/images/copilot-0a.png" alt="Copilot config" width=400/>

Open the Copilot chat, select 'Agent' instead of 'Ask', and choose your preferred AI model. You should see `mcp.json` added to the context.

<img src="docs/images/copilot-0b.png" alt="Fashion visualize"/>

### Example
Let's try running the same example as above.

<details>
<summary>Click to expand the VSCode + Copilot example</summary>

First, we look for some fashion-related datasets. Copilot figures out we can use Eclair for this and asks for permission to use the `search-datasets` tool.
<img src="docs/images/copilot-1.png" alt="Fashion search"/>

This returns a long list of fashion-related datasets (only a few are shown here).
<img src="docs/images/copilot-2.png" alt="Fashion list"/>

Next, we ask it to download and visualize it. Copilot identifies Eclair's `download-dataset` tool to do this, and chooses to generate a Jupyter notebook with the code and visualizations. Eclair provides the required metadata and download instructions to get this right.
<img src="docs/images/copilot-3.png" alt="Fashion download"/>
<img src="docs/images/copilot-4.png" alt="Fashion notebook permission"/>

Thanks to the Eclair instructions, Copilot can write the correct code, and when the notebook is run, the requestion visualization is done.
<img src="docs/images/copilot-6.png" alt="Fashion notebook"/>
<img src="docs/images/copilot-7.png" alt="Fashion visualize"/>

Copilot concludes the task with a summary, and suggestions for next steps to further analyse this dataset.
<img src="docs/images/copilot-5.png" alt="Fashion summary"/>

</details>


### With VSCode and Google Code Assist

First, install [Gemini Code Assist](https://marketplace.visualstudio.com/items?itemName=Google.geminicodeassist) (if you haven't already)

To enable Agentic mode, in the VSCode search bar, enter ‘> Open User Settings JSON’. Then, in the JSON settings, add

```json
   "geminicodeassist.updateChannel": "Insiders",
```

Identically to Gemini CLI, 
* set your Gemini API key in an .env file
```bash
echo "GEMINI_API_KEY=XXX" >> .env
```

* add the MCP server in `~/.gemini/settings.json`
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

* copy the system prompt to your local working directory.
```bash
cp src/eclair/client/gemini/gemini.md ./GEMINI.md
```

Restart VSCode, open the Gemini Sidebar (sparkle icon), set Gemini to Agentic mode, and check whether the MCP server is loaded by entering `/mcp` in the prompt. It should look like this:

<img src="docs/images/gca.png" alt="GCA" width=400/>

You can now start querying with Eclair support.

### Example
Let's try running the same example as above.

<details>
<summary>Click to expand the VSCode + Gemini Code Assist example</summary>

Gemini immediately calls the Eclair `search-datasets` tool to find relevant datasets.
It automatically proceeds to generate a Jupyter notebook with the requested visualizations.
<img src="docs/images/gca-1.png" alt="Fashion search"/>

Gemini uses the metadata and instructions from Eclair to download the dataset.
The notebook details every step of the process.
<img src="docs/images/gca-2.png" alt="Fashion download"/>

At the end of the notebook, it returns the requested visualization.
<img src="docs/images/gca-3.png" alt="Fashion visualize"/>

</details>


## Python API
By importing the Eclair Python package, you can integrate all Eclair tools into your code and Jupyter notebooks.

To use AI models in combination with Eclair, you also need to set your AI model's API key and system prompt. For instance, for Gemini, do the following (replace XXX with your API key):

```bash
echo "GEMINI_API_KEY=XXX" >> .env
echo "GEMINI_SYSTEM_MD="src/eclair/client/gemini/gemini.md" >> .env
```

### Basic Usage

This example shows how to run the search-datasets tool in Python. Other tools are called similarly.
```python
import asyncio
import json
from eclair.client import EclairClient

async def main():
    # Create a python client
    # Include the URL where your server is running
    client = EclairClient("http://localhost:8080/mcp")

    # Run the `search-datasets` tool  
    datasets = await client.search_datasets("mnist")
    
    # Parse results
    for i, ds in enumerate(datasets.content, 1):
        doc = json.loads(ds.text)['document']
        print(f"{i}. {doc['collection_name']}/{doc['entity_name']}")

asyncio.run(main())
```

<details>
<summary>Click to expand the output</summary>

> 1. ylecun/mnist
> 2. VedantPadwal/mnist
> 3. ChristianOrr/mnist
> 4. severo/mnist
> 5. barkermrl/mnist-c
> 6. louisraedisch/AlphaNum
> 7. RomanShp/MNIST-ResNet-Demo-Data
> 8. Fraser/mnist-text-small
> 9. MagedSaeed/MADBase
> ...

</details>

### Data workflows
In the same way you can combine tools for more complex workflows, such as searching for datasets, checking the meta-data, and downloading it.
```python
async def dataset_workflow():
    client = EclairClient("http://localhost:8080/mcp")
    
    # Search for MNIST datasets
    response = await client.search_datasets("mnist")
    datasets = response.content
    print(f"Found {len(datasets)} MNIST-like datasets")
    
    # Get Croissant metadata for a specific dataset
    response = await client.serve_croissant("ylecun", "mnist")
    metadata = response.content[0].text
    print("Dataset metadata:", metadata,'...')
    
    # Get download information
    response = await client.download_dataset("ylecun", "mnist")
    download_info = json.loads(response.content[0].text)
    print("Download details:", list(download_info.keys()))
    print("Download instructions:", download_info["instructions"])

    # Get preview URL if available
    response = await client.datasets_preview_url("ylecun", "mnist")
    preview_url = response.content[0].text
    print(f"Preview URL: {preview_url}")

asyncio.run(dataset_workflow())
```
Output below. This gives you an overview of relevant datasets, detailed metadata for each, download instructions (including code), and a link to preview a sample of the dataset.

<details>
<summary>Click to expand the output</summary>

```
Found 23 MNIST-like datasets
```
```
Dataset metadata: {
  "url": "https://huggingface.co/datasets/ylecun/mnist",
  "name": "mnist",
  "@type": "sc:Dataset ...
```
```
Download details: ['metadata', 'asset_origin', 'data_path', 'instructions']
Download instructions: 
```
``` python
# Install if necessary
# !pip install datasets pandas

from datasets import load_dataset
import pandas as pd

# 1. Load a sample dataset from Hugging Face
dataset = load_dataset("ylecun/mnist")

# 2. Convert to a pandas DataFrame for easier exploration
df_train = pd.DataFrame(dataset["train"])

print("\nPandas DataFrame Head:")
print(df_train.head())
```
```
Preview URL: https://dock.jetty.io/api/v1/datasets/ylecun/mnist/preview
```

</details>



### Dataset Validation

This is how you can use the Croissant validation tool:"
```python
import asyncio
import json
from eclair.client import EclairClient

async def validate_dataset():
    client = EclairClient("http://localhost:8080/mcp")

    # First get some metadata to validate from OpenML
    response = await client.serve_croissant("Albert-Bifet", "covertype")
    croissant = response.content[0].text
    print(croissant)

    # Validate the Croissant metadata
    validation_result = await client.validate_croissant(croissant)
    print("Validation result:")
    print(json.dumps(json.loads(validation_result.content[0].text), indent=2))

asyncio.run(validate_dataset())
```

Output: The metadata is valid Croissant and we can automatically load the dataset.

<details>
<summary>Click to expand the output</summary>

```json
{
  "valid": true,
  "results": [
    {
      "test": "JSON Format Validation",
      "passed": true,
      "message": "The string is valid JSON.",
      "status": "pass"
    },
    {
      "test": "Croissant Schema Validation",
      "passed": true,
      "message": "The dataset passes Croissant validation.",
      "status": "pass"
    },
    {
      "test": "Records Generation Test",
      "passed": true,
      "message": "Record set 'enumerations/class' passed validation.
      "status": "pass"
    }
  ]
}
```
</details>


### Using AI models
MCP tools are especially powerful if we give them to AI models, so we can ask complex questions in natural language. Eclair offers a number of clients to facilitate this, such as `GeminiMCPClient`, and you can easily create new clients using FastMCP.

#### Basic questions
First, a simple request to find interesting datasets. The AI model decides automatically which Eclair tools to use.

``` python
from eclair.client.gemini import GeminiMCPClient
import asyncio

async def ai_assistant():
    client = GeminiMCPClient()
    await client.initialize()
    
    # Let Gemini understand and execute complex requests
    response = await client.ask_gemini_with_tools(
        "Find me datasets on tree covertype in national forests in the USA"
        "and tell me which one has the best information on tree coverage at different elevations."
    )
    print(response)

asyncio.run(ai_assistant())
```

<details>
<summary>Click to expand the AI response</summary>

> Of course. I have analyzed the search results for datasets on tree covertype in US national forests.
> 
> While the request was for multiple datasets, my search returned one highly relevant and comprehensive dataset that is well-known for this type of analysis. Here is a breakdown of my findings and my recommendation.
> 
> ### Dataset Found:
> 
> **1. Covertype Dataset**
> 
> *   **Summary:** This is a classic dataset used for predicting forest cover type from cartographic variables. The data was collected from four wilderness areas within the **Roosevelt National Forest** in northern Colorado. Each data point represents a 30x30 meter cell.
> *   **Source:** The data originates from the US Forest Service (USFS) and the US Geological Survey (USGS).
> *   **Key Features:**
>     *   **Elevation:** Measured in meters.
>     *   **Aspect:** The direction of the slope, in degrees.
>     *   **Slope:** The steepness of the slope, in degrees.
>     *   **Distance to Hydrology/Roadways/Fire Points:** Horizontal and vertical distances to various landmarks.
>     *   **Wilderness Area:** 4 binary columns indicating which of the four wilderness areas the cell belongs to.
>     *   **Soil Type:** 40 binary columns for different soil types.
>     *   **Cover\_Type:** The target variable, an integer from 1 to 7 representing the dominant tree species (e.g., Spruce/Fir, Lodgepole Pine, Ponderosa Pine).
> 
> ---
> 
> ### Recommendation:
>
> Based on your specific interest in analyzing tree coverage at different elevations, the **Covertype dataset is an excellent choice**.
> 
> Here’s why it has the best information for your needs among the results:
> 1.  **Direct Elevation Data:** The dataset includes a quantitative `Elevation` feature, measured in meters. This allows you to directly correlate specific elevations with different tree cover types.
> 2.  **Rich Contextual Information:** The description explicitly states that the four wilderness areas included in the study have different mean elevations and, as a result, different dominant tree species.
> 3.  **Granularity:** The data is provided at a 30x30 meter cell resolution, which is granular enough to perform detailed analysis on how cover types change with elevation, slope, and aspect.
> 
> This dataset is perfectly suited for tasks like creating elevation bands (e.g., low, medium, high) and then analyzing the distribution of the 7 different `Cover_Type` classes within each band. I would strongly recommend starting your analysis with this dataset.

</details>

#### Deeper questions
You can also create complex request, or let the AI model itself figure out how to answer a complex question given the available tools.

``` python
async def smart_dataset_workflow():
    client = GeminiMCPClient()
    await client.initialize()
    
    # Complex dataset analysis and recommendation
    recommendation = await client.ask_gemini_with_tools("""
        I need to build a model for recognizing handwritten digits. 
        Please:
        1. Find suitable datasets for this task
        2. Get metadata including their sizes, formats, and quality
        3. Provide code to download this data
    """)
    
    print(recommendation)
```

<details>
<summary>Click to expand the AI response</summary>

> Of course. I have analyzed the search results for datasets suitable for building a handwritten digit recognition model. Here is a summary of the findings, my recommendations, and the code to get you started.
> 
> ### 1. Suitable Datasets
> 
> Based on the search, the most suitable and widely-used dataset for your task is the **MNIST (Modified National Institute of Standards and Technology) dataset**. Several versions of this dataset were found, with the most authoritative and easiest to use being:
> 
> *   **`ylecun/mnist`**: Hosted on the Hugging Face Hub. This is the original MNIST dataset provided by one of its creators, Yann LeCun. It's the recommended choice due to its ease of access via the `datasets` library.
> *   **`Yann-LeCun/mnist_784`**: Hosted on OpenML. This is the same classic dataset, accessible through libraries like Scikit-learn.
> 
> These datasets are the standard benchmark for digit recognition and are perfect for your project.
> 
> ### 2. Metadata and Analysis
> 
> Here is a breakdown of the recommended datasets.
> 
> | Dataset Name | `ylecun/mnist` (Hugging Face) | `Yann-LeCun/mnist_784` (OpenML) |
> | :--- | :--- | :--- |
> | **Description** | The classic dataset of 70,000 handwritten digits (0-9). | The same classic dataset, with each image flattened into 784 features. |
> | **Size** | - **Total Images**: 70,000<br>- **Training Set**: 60,000 images<br>- **Test Set**: 10,000 images | - **Total Images**: 70,000<br>- **Training Set**: 60,000 examples<br>- **Test Set**: 10,000 examples |
> | **Format** | - **Images**: 28x28 grayscale `PIL.Image` objects.<br>- **Labels**: Integers from 0 to 9. | - **Data**: 70,000 rows x 784 columns (flattened 28x28 images).<br>- **Labels**: String representations of digits '0' through '9'. |
> | **Quality** | High. This is the canonical, pre-processed dataset that has been used to benchmark thousands of machine learning models. The images are size-normalized and centered. | High. Same data source and quality as the Hugging Face version. It is a well-structured and clean dataset. |
> | **Best For** | Projects using modern deep learning frameworks like PyTorch or TensorFlow, as the Hugging Face `datasets` library integrates seamlessly with them. | Projects using traditional machine learning or Scikit-learn, where a simple feature matrix (`X`) and target vector (`y`) are preferred. |
> 
> ---
> 
> #### Other Datasets Found (Less Suitable)
> 
> *   **`Kaggle/SignMNIST`**: This dataset is for **American Sign Language letters**, not handwritten digits. While it's inspired by MNIST, it's for a different task.
> *   **`Isabelle-Guyon/gina_agnostic`**: This is a more complex, modified version of MNIST created for a specific machine learning challenge (distinguishing odd vs. even numbers from pairs of digits). It is not suitable for standard 10-class digit recognition.
> *   **`MagedSaeed/MADBase`**: This dataset contains **Arabic handwritten digits**, which is a different character set from the standard 0-9 digits you likely intend to recognize.
> 
> ---
> 
> ### 3. Code to Download the Data
> 
> #### Using the Hugging Face `datasets` library
> 
> This is the best option if you plan to use deep learning frameworks.
> 
> First, install the library:
> ```bash
> pip install datasets
> ```
> 
> Then, use this Python code to download and inspect the data:
> ```python
> from datasets import load_dataset
> 
> # Load the MNIST dataset from the Hugging Face Hub
> mnist_dataset = load_dataset("ylecun/mnist")
> 
> # You can easily access the training and testing splits
> train_data = mnist_dataset["train"]
> test_data = mnist_dataset["test"]
> 
> # Let's look at a single example
> example = train_data[0]
> image = example['image']
> label = example['label']
> 
> print(f"\nExample label: {label}")
> print(f"Image size: {image.size}")
> print(f"Image mode: {image.mode}")
> 
> # To display the image (requires matplotlib and Pillow)
> # pip install matplotlib Pillow
> import matplotlib.pyplot as plt
> 
> plt.imshow(image, cmap='gray')
> plt.title(f"Label: {label}")
> plt.show()
> ```
> 
> #### Using OpenML and Scikit-learn
> 
> This is a great option if you are using Scikit-learn for your modeling.
> 
> First, ensure you have Scikit-learn installed:
> ```bash
> pip install scikit-learn
> ```
> 
> Then, use this code to download the `mnist_784` dataset from OpenML:
> ```python
> from sklearn.datasets import fetch_openml
> import numpy as np
> import matplotlib.pyplot as plt
> 
> # Fetch the dataset from OpenML.
> # as_frame=False returns NumPy arrays instead of a Pandas DataFrame
> mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')
> 
> # The data is in a dictionary-like object
> # 'data' contains the flattened images (features)
> # 'target' contains the labels
> X = mnist.data
> y = mnist.target
> 
> print(f"Data shape (X): {X.shape}")   # (70000, 784)
> print(f"Target shape (y): {y.shape}") # (70000,)
> print(f"Data type: {X.dtype}")        # float64
> print(f"Target type: {y.dtype}")      # object (strings)
> 
> # Note: The labels are strings, so you might want to convert them to integers
> y = y.astype(np.uint8)
> print(f"Target type after conversion: {y.dtype}") # uint8
> 
> # Split the data into training and test sets as is standard for MNIST
> X_train, X_test = X[:60000], X[60000:]
> y_train, y_test = y[:60000], y[60000:]
> 
> print(f"\nTraining data shape: {X_train.shape}")
> print(f"Test data shape: {X_test.shape}")
> 
> # To visualize an image, you need to reshape it from 784 to 28x28
> first_image = X_train[0]
> first_image_reshaped = first_image.reshape(28, 28)
> first_label = y_train[0]
> 
> plt.imshow(first_image_reshaped, cmap='gray')
> plt.title(f"Label: {first_label}")
> plt.show()
> ```

</details>

Take 5 minutes to think about your own deep questions you could answer with Eclair.



## Command Line Interface
Finally, you can also directly interact with the MCP tools via the command-line client.

To use AI models (see below), you also need to set your AI model's API key and system prompt. For instance, for Gemini, do the following (replace XXX with your API key):

```bash
echo "GEMINI_API_KEY=XXX" >> .env
echo "GEMINI_SYSTEM_MD="src/eclair/client/gemini/gemini.md" >> .env
```

```bash
# Test server connectivity
eclair-client --tool ping

# Search for datasets
eclair-client --tool search-datasets --query "mnist"
```

This also works with AI model integrations, e.g. with the `use-gemini` argument:
```bash
# Use with Gemini
eclair-client --use-gemini --tool ask --query "Find datasets for image segmentation"

# Short form
eclair-client -G -T ask -Q "Find datasets for image segmentation"
```

> TODO: The CLI interface currently doesn't keep a conversation state between commands. Use the IDE integrations and AI agents below for longer conversations with memory.


Overview of argments and shortcuts:

| Long Form | Short Form | Description |
|-----------|------------|-------------|
| `--server-url` | `-S` | MCP server URL |
| `--tool` | `-T` | Tool to call |
| `--query` | `-Q` | Query string for search-datasets |
| `--collection` | `-C` | Dataset collection |
| `--dataset` | `-D` | Dataset name |
| `--use-gemini` | `-G` | Use Gemini client |
| `--use-claude` | `-L` | Use Claude client |


### Example
Command:
```bash
eclair-client -GT ask -Q "look for interesting datasets for image segmentation and order by size"
```

<details>
<summary>Click to expand the AI response</summary>

> Of course! I'd be happy to help you find interesting datasets for image segmentation. Let's get started right away.
> 
> First, I'll search for datasets related to "image segmentation" on the eclair server. Then, I'll analyze their metadata to determine their size and present them to you in descending order.
> 
> Excellent! The search returned a great list of potential datasets. Now, I will retrieve the Croissant metadata for each of these to find their sizes and other relevant details. This might take a moment as I need to query each one individually.
> 
> Fantastic! I've successfully retrieved the metadata and extracted the sizes for each dataset. Here is the list of image segmentation datasets, ordered from largest to smallest:
> 
> 1.  **`segments/sam-1b`**
>     *   **Size**: 12.3 TB
>     *   **Description**: The Segment Anything 1-Billion mask dataset (SA-1B). A massive, high-quality dataset with over 1 billion masks on 11 million images, designed for developing foundational models in computer vision.
> 
> 2.  **`google/cityscapes`**
>     *   **Size**: ~11.2 GB (11.0 GB + 241.0 MB)
>     *   **Description**: A large-scale dataset focusing on semantic understanding of urban street scenes from 50 different cities. It's a standard benchmark for autonomous driving applications.
> 
> 3.  **`segments/sidewalk-semantic`**
>     *   **Size**: 1.8 GB
>     *   **Description**: A collection of images focused on urban sidewalks with detailed semantic segmentation. Crucial for applications like autonomous robot navigation and accessibility tools.
> 
> 4.  **`scene_parse_150`**
>     *   **Size**: 1.0 GB
>     *   **Description**: A benchmark for scene parsing, providing densely annotated images with pixel-level labels for a wide range of objects and scenes.
> 
> 5.  **`augmented-traffic-signs`**
>     *   **Size**: 1.0 GB
>     *   **Description**: Contains 1000 images of traffic signs (1280x720) with segmentation masks, split into training and test sets.
> 
> 6.  **`facebook/ade20k`**
>     *   **Size**: 887.0 MB
>     *   **Description**: A large-scale scene parsing benchmark with a diverse set of images and dense annotations for objects and their parts.
> 
> 7.  **`nielsr/ade20k-panoptic`**
>     *   **Size**: 887.0 MB
>     *   **Description**: A panoptic version of the ADE20K dataset, providing annotations for both semantic "stuff" (like sky, road) and instance "things" (like individual cars, people).
> 
> 8.  **`kvasir-v2`**
>     *   **Size**: 495.0 MB
>     *   **Description**: A diverse dataset of medical images from the gastrointestinal tract, annotated by experts for developing computer-aided diagnosis systems.
> 
> 9.  **`kvasir-instrument`**
>     *   **Size**: 80.0 MB
>     *   **Description**: A dataset of images from colonoscopy procedures, with segmentation masks for various medical instruments. Useful for computer-assisted surgery applications.
> 
> 10. **`fashion-mnist`**
>     *   **Size**: 31.0 MB
>     *   **Description**: A dataset of 70,000 28x28 grayscale images of clothing items. While primarily for classification, it can be used for simple segmentation tasks.
> 
> This list should give you a great starting point! The `sam-1b` dataset is exceptionally large and state-of-the-art, while `cityscapes` and `ade20k` are very popular and well-established benchmarks.
</details>

Eclair can be integrated in many more ways. Let us know your ideas!

# Development

## Code structure

To modify the MCP server or add new tools:
* See `src/eclair/server`
    * `server.py` sets up the MCP server itself
    * `tools.py` contains tool implementations
    * `validation.py` contains the Croissant validation
    * `/context` contains context for AI agents, such as persona, the Croissant spec, and usage guidelines.

To modify or create new MCP clients:
* See `src/eclair/client`
    * `server.py` implements the Python client
    * `cli.py` implements the Command Line Interface
    * `/gemini` contains the Gemini integration
    * `/{model}` idem for other model integrations


Configure upstream server settings in `config.json`

Build and install: `pip install -e .`

Stay awesome. Be a bit better than you were yesterday.

## Testing

Eclair includes comprehensive testing capabilities that can be run both as standalone scripts and with pytest.

Note: the tests will automatically start the server before the test and stop it afterward. Hence, the test server should not be running before starting the tests.

### Using pytest (Recommended)

Run all tests with pytest for comprehensive testing:
```bash
# Run all tests
pytest tests/ -v

# Run specific tests
pytest tests/test_server.py -v
pytest tests/test_client.py -v

# Run tests with coverage (if pytest-cov is installed)
pytest tests/ --cov=src/eclair --cov-report=html
```

### Standalone Script Execution

Each test can also be run directly as a Python script. For instance:

Test whether the MCP server and all Eclair tools work:
```bash
python tests/test_server.py
```

Test the Eclair client functionality:
```bash
python tests/test_client.py
```

## Building and Installing

### Build the Package
```bash
# Build using the provided script
./build.sh

# Or manually with Python build tools  
python -m build
```

### Install from Local Build
```bash
pip install dist/eclair-0.0.1-py3-none-any.whl
```

### Development Installation
```bash
pip install -e .
```

## Contributors
* Joaquin Vanschoren (TU Eindhoven, OpenML, Google Deepmind)
* Omar Benjelloun (Google Deepmind)
* Jon Lebenshold (Jetty)
* Natasha Noy (Google)
* Luis Oala

Thank you for supporting Eclair! 🙂