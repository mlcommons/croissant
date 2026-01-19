# Python API Reference

Eclair provides a comprehensive Python API for programmatic access to dataset discovery, downloading, and metadata validation. This is perfect for automation, batch processing, and integration into data pipelines.

## Installation

Install Eclair with Python API support:

```bash
pip install eclair
```

Alternatively, install the development version from source code:

```bash
git clone https://github.com/mlcommons/croissant.git
cd croissant/eclair
pip install -e .
```

## Quick Start

The code below creates an Eclair python client, searches for datasets, retrieves metadata, 
and retrieves download instructions.

All methods are **async** and return `CallToolResult` objects. Access the data through the 
`structured_content['result']` property.


```python
import asyncio
from eclair.client import EclairClient

async def main():
    # Create client instance
    client = EclairClient()
    
    # Test connectivity
    result = await client.ping()
    print(f"Server status: {result.structured_content['result']}")
    
    # Search for datasets
    datasets = await client.search_datasets("computer vision")
    print(f"Found {len(datasets.structured_content['result'])} datasets")
    
    # Get dataset metadata (Croissant format)
    metadata_result = await client.serve_croissant("ylecun", "mnist")
    metadata = metadata_result.structured_content['result']
    print(f"Data description: {metadata.get('description', 'N/A')[:200]}...")
    
    # Download dataset information
    download_result = await client.download_dataset("ylecun", "mnist")
    download_info = download_result.structured_content['result']
    print(download_info['instructions'][:300])

# Run the async function
asyncio.run(main())
```

<details>
<summary>Click to expand the output</summary>

```bash
Server status: Pong! Eclair MCP Server is running successfully.
Found 40 datasets

Data description: Dataset Card for MNIST
The MNIST dataset consists of 70,000 28x28 black-and-white images of handwritten digits...

# Install if necessary
# !pip install datasets pandas
from datasets import load_dataset

# 1. Load this dataset from Hugging Face
dataset = load_dataset("ylecun/mnist")
...
```

</details>

## API Reference Summary

| Method | Purpose | Returns |
|--------|---------|---------|
| `ping()` | Test server connectivity | "pong" if server is responsive |
| `search_datasets(query)` | Search for datasets | List of matching datasets |
| `download_dataset(collection, dataset)` | Download a dataset | Success/failure status |
| `serve_croissant(collection, dataset)` | Get dataset metadata | Croissant JSON metadata |
| `validate_croissant(metadata)` | Validate metadata format | Validation results with errors |
| `datasets_preview_url(collection, dataset)` | Get dataset preview URL | URL string for preview |
| `get_help()` | Get server help information | Help text and usage info |

All methods are **async** and return `CallToolResult` objects. Access the actual data via `.structured_content['result']`.

### Basic Configuration

```python
from eclair.client import EclairClient

# Uses default server URL (http://localhost:8080/mcp)
client = EclairClient()

# Alternatively, connect to a local or remote server
client = EclairClient("http://192.168.1.100:8080/mcp")
```

### Search Datasets

Search for datasets using natural language queries:

```python
async def search_example():
    client = EclairClient()

    # Search with various types of queries
    cv_results = await client.search_datasets("computer vision")
    nlp_results = await client.search_datasets("natural language processing")
    mnist_results = await client.search_datasets("handwritten digits")

    # Access the results
    datasets = cv_results.structured_content['result']
    for dataset in datasets[:3]:  # Show first 3 results
        dataset = dataset['document']
        print(f"Collection: {dataset['collection_name']}")
        print(f"Dataset: {dataset['entity_name']}")
        print(f"URL: {dataset['metadata']['url']}")
        print("---")

asyncio.run(search_example())
```

<details>
<summary>Click to expand the output</summary>

```
Collection: mbateman
Dataset: github-issues
URL: https://huggingface.co/datasets/mbateman/github-issues
---
Collection: djghosh
Dataset: wds_vtab-dtd_test
URL: https://huggingface.co/datasets/djghosh/wds_vtab-dtd_test
---
Collection: cansa
Dataset: Describable-Textures-Dataset-DTD
URL: https://huggingface.co/datasets/cansa/Describable-Textures-Dataset-DTD
---
```
</details>

### Download Dataset

Download datasets to your local machine:

```python
async def download_example():
    client = EclairClient()

    # Download Fashion-MNIST dataset
    result = await client.download_dataset("ylecun", "mnist")
    print(result.structured_content)

asyncio.run(download_example())
```
<details>
<summary>Click to expand the output</summary>

```json
{'result': 
    {'metadata': 
        {'url': 'https://huggingface.co/datasets/ylecun/mnist',
         'name': 'mnist', 
         '@type': 'sc:Dataset', 
         'sameAs': 'http://yann.lecun.com/exdb/mnist/', 
         'license': 'https://choosealicense.com/licenses/mit/', 
         ...
```
</details>

### Get Dataset Metadata (Croissant Format)

Retrieve dataset metadata in Croissant JSON format:

```python
async def metadata_example():
    client = EclairClient()
    
    # Get MNIST metadata
    result = await client.serve_croissant("ylecun", "mnist")
    metadata = result.structured_content['result']
    
    # Display key information
    print(f"Description: {metadata.get('description', 'N/A')}")
    print(f"License: {metadata.get('license', 'N/A')}")
    
    # Show distribution information
    if 'distribution' in metadata:
        for dist in metadata['distribution']:
            print(f"File: {dist.get('name', 'N/A')}")
            print(f"Format: {dist.get('encodingFormat', 'N/A')}")
            print(f"URL: {dist.get('contentUrl', 'N/A')}")

asyncio.run(metadata_example())
```
<details>
<summary>Click to expand the output</summary>
```
Description: Dataset Card for MNIST
The MNIST dataset consists of 70,000 28x28 black-and-white images of handwritten digits extracted from two NIST databases. There are 60,000 images in the training dataset and 10,000 images in the validation dataset, one class per digit so a total of 10 classes, with 7,000 images (6,000 train images and 1,000 test images) per class...
License: https://choosealicense.com/licenses/mit/
File: repo
Format: git+https
URL: https://huggingface.co/datasets/ylecun/mnist/tree/refs%2Fconvert%2Fparquet
```
</details>

### Validate Croissant Metadata

Validate Croissant JSON metadata for correctness:

```python
async def validation_example():
    client = EclairClient()
    
    # Example metadata to validate
    sample_metadata = {
        "@id": "test-dataset",
        "name": "Test Dataset",
        "description": "A sample dataset for testing",
        "license": "CC0-1.0"
    }
    
    # Validate the metadata
    result = await client.validate_croissant(sample_metadata)
    validation_result = result.structured_content['result']
    
    if validation_result.get('valid', False):
        print("✅ Metadata is valid!")
    else:
        print("❌ Metadata validation failed:")
        for error in validation_result.get('errors', []):
            print(f"  - {error}")

asyncio.run(validation_example())
```

### Get Dataset Preview URL

Get a preview URL for exploring dataset contents.

!!! info "Experimental"
    This feature is experimental and will not work for all datasets.

```python
async def preview_example():
    client = EclairClient()
    
    # Get preview URL for Fashion-MNIST
    result = await client.datasets_preview_url("ylecun", "fashion-mnist")
    preview_url = result.structured_content['result']
    
    print(f"Dataset preview available at: {preview_url}")
    
    # You can then open this URL in a browser or use requests to fetch content

asyncio.run(preview_example())
```

### Check Server Status

Test connectivity and server health:

```python
async def health_check():
    client = EclairClient()
    
    # Ping the server
    result = await client.ping()
    status = result.structured_content['result']
    
    if status == "pong":
        print("✅ Eclair server is running and responsive")
    else:
        print("❌ Server connectivity issue")

asyncio.run(health_check())
```

### Get Help Information

Retrieve help and usage information:

```python
async def help_example():
    client = EclairClient()
    
    # Get help information
    result = await client.get_help()
    help_content = result.structured_content['result']
    
    print("Eclair Server Help:")
    print(help_content)

asyncio.run(help_example())
```

## Basic Examples

### Dataset Search
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
```
1. ylecun/mnist
2. VedantPadwal/mnist
3. ChristianOrr/mnist
4. severo/mnist
5. barkermrl/mnist-c
6. louisraedisch/AlphaNum
7. RomanShp/MNIST-ResNet-Demo-Data
8. Fraser/mnist-text-small
9. MagedSaeed/MADBase
...
```
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


## Using AI models
MCP tools are especially powerful if we give them to AI models, so we can ask complex questions in natural language. Eclair offers a number of clients to facilitate this, such as `GeminiMCPClient`, and you can easily create new clients using FastMCP.


To use AI models in combination with Eclair, you also need to set your AI model's API key and system prompt. For instance, for Gemini, do the following (replace XXX with your API key):

```bash
echo "GEMINI_API_KEY=XXX" >> .env
echo "GEMINI_SYSTEM_MD="src/eclair/client/gemini/gemini.md" >> .env
```

### Basic questions
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

Of course. I have analyzed the search results for datasets on tree covertype in US national forests.

While the request was for multiple datasets, my search returned one highly relevant and comprehensive dataset that is well-known for this type of analysis. Here is a breakdown of my findings and my recommendation.

### Dataset Found:

**1. Covertype Dataset**

*   **Summary:** This is a classic dataset used for predicting forest cover type from cartographic variables. The data was collected from four wilderness areas within the **Roosevelt National Forest** in northern Colorado. Each data point represents a 30x30 meter cell.
*   **Source:** The data originates from the US Forest Service (USFS) and the US Geological Survey (USGS).
*   **Key Features:**
    *   **Elevation:** Measured in meters.
    *   **Aspect:** The direction of the slope, in degrees.
    *   **Slope:** The steepness of the slope, in degrees.
    *   **Distance to Hydrology/Roadways/Fire Points:** Horizontal and vertical distances to various landmarks.
    *   **Wilderness Area:** 4 binary columns indicating which of the four wilderness areas the cell belongs to.
    *   **Soil Type:** 40 binary columns for different soil types.
    *   **Cover\_Type:** The target variable, an integer from 1 to 7 representing the dominant tree species (e.g., Spruce/Fir, Lodgepole Pine, Ponderosa Pine).

---

### Recommendation:

Based on your specific interest in analyzing tree coverage at different elevations, the **Covertype dataset is an excellent choice**.

Here’s why it has the best information for your needs among the results:
1.  **Direct Elevation Data:** The dataset includes a quantitative `Elevation` feature, measured in meters. This allows you to directly correlate specific elevations with different tree cover types.
2.  **Rich Contextual Information:** The description explicitly states that the four wilderness areas included in the study have different mean elevations and, as a result, different dominant tree species.
3.  **Granularity:** The data is provided at a 30x30 meter cell resolution, which is granular enough to perform detailed analysis on how cover types change with elevation, slope, and aspect.

This dataset is perfectly suited for tasks like creating elevation bands (e.g., low, medium, high) and then analyzing the distribution of the 7 different `Cover_Type` classes within each band. I would strongly recommend starting your analysis with this dataset.

</details>

### Deeper questions
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

Of course. I have analyzed the search results for datasets suitable for building a handwritten digit recognition model. Here is a summary of the findings, my recommendations, and the code to get you started.

### 1. Suitable Datasets

Based on the search, the most suitable and widely-used dataset for your task is the **MNIST (Modified National Institute of Standards and Technology) dataset**. Several versions of this dataset were found, with the most authoritative and easiest to use being:

*   **`ylecun/mnist`**: Hosted on the Hugging Face Hub. This is the original MNIST dataset provided by one of its creators, Yann LeCun. It's the recommended choice due to its ease of access via the `datasets` library.
*   **`Yann-LeCun/mnist_784`**: Hosted on OpenML. This is the same classic dataset, accessible through libraries like Scikit-learn.

These datasets are the standard benchmark for digit recognition and are perfect for your project.

### 2. Metadata and Analysis

Here is a breakdown of the recommended datasets.

| Dataset Name | `ylecun/mnist` (Hugging Face) | `Yann-LeCun/mnist_784` (OpenML) |
| :--- | :--- | :--- |
| **Description** | The classic dataset of 70,000 handwritten digits (0-9). | The same classic dataset, with each image flattened into 784 features. |
| **Size** | - **Total Images**: 70,000<br>- **Training Set**: 60,000 images<br>- **Test Set**: 10,000 images | - **Total Images**: 70,000<br>- **Training Set**: 60,000 examples<br>- **Test Set**: 10,000 examples |
| **Format** | - **Images**: 28x28 grayscale `PIL.Image` objects.<br>- **Labels**: Integers from 0 to 9. | - **Data**: 70,000 rows x 784 columns (flattened 28x28 images).<br>- **Labels**: String representations of digits '0' through '9'. |
| **Quality** | High. This is the canonical, pre-processed dataset that has been used to benchmark thousands of machine learning models. The images are size-normalized and centered. | High. Same data source and quality as the Hugging Face version. It is a well-structured and clean dataset. |
| **Best For** | Projects using modern deep learning frameworks like PyTorch or TensorFlow, as the Hugging Face `datasets` library integrates seamlessly with them. | Projects using traditional machine learning or Scikit-learn, where a simple feature matrix (`X`) and target vector (`y`) are preferred. |

---

#### Other Datasets Found (Less Suitable)

*   **`Kaggle/SignMNIST`**: This dataset is for **American Sign Language letters**, not handwritten digits. While it's inspired by MNIST, it's for a different task.
*   **`Isabelle-Guyon/gina_agnostic`**: This is a more complex, modified version of MNIST created for a specific machine learning challenge (distinguishing odd vs. even numbers from pairs of digits). It is not suitable for standard 10-class digit recognition.
*   **`MagedSaeed/MADBase`**: This dataset contains **Arabic handwritten digits**, which is a different character set from the standard 0-9 digits you likely intend to recognize.

---

### 3. Code to Download the Data

#### Using the Hugging Face `datasets` library

This is the best option if you plan to use deep learning frameworks.

First, install the library:
```bash
pip install datasets
```

Then, use this Python code to download and inspect the data:
```python
from datasets import load_dataset

# Load the MNIST dataset from the Hugging Face Hub
mnist_dataset = load_dataset("ylecun/mnist")

# You can easily access the training and testing splits
train_data = mnist_dataset["train"]
test_data = mnist_dataset["test"]

# Let's look at a single example
example = train_data[0]
image = example['image']
label = example['label']

print(f"\nExample label: {label}")
print(f"Image size: {image.size}")
print(f"Image mode: {image.mode}")

# To display the image (requires matplotlib and Pillow)
# pip install matplotlib Pillow
import matplotlib.pyplot as plt

plt.imshow(image, cmap='gray')
plt.title(f"Label: {label}")
plt.show()
```

### Using OpenML and Scikit-learn

This is a great option if you are using Scikit-learn for your modeling.

First, ensure you have Scikit-learn installed:
```bash
pip install scikit-learn
```

Then, use this code to download the `mnist_784` dataset from OpenML:
```python
from sklearn.datasets import fetch_openml
import numpy as np
import matplotlib.pyplot as plt

# Fetch the dataset from OpenML.
# as_frame=False returns NumPy arrays instead of a Pandas DataFrame
mnist = fetch_openml('mnist_784', version=1, as_frame=False, parser='auto')

# The data is in a dictionary-like object
# 'data' contains the flattened images (features)
# 'target' contains the labels
X = mnist.data
y = mnist.target

print(f"Data shape (X): {X.shape}")   # (70000, 784)
print(f"Target shape (y): {y.shape}") # (70000,)
print(f"Data type: {X.dtype}")        # float64
print(f"Target type: {y.dtype}")      # object (strings)

# Note: The labels are strings, so you might want to convert them to integers
y = y.astype(np.uint8)
print(f"Target type after conversion: {y.dtype}") # uint8

# Split the data into training and test sets as is standard for MNIST
X_train, X_test = X[:60000], X[60000:]
y_train, y_test = y[:60000], y[60000:]

print(f"\nTraining data shape: {X_train.shape}")
print(f"Test data shape: {X_test.shape}")

# To visualize an image, you need to reshape it from 784 to 28x28
first_image = X_train[0]
first_image_reshaped = first_image.reshape(28, 28)
first_label = y_train[0]

plt.imshow(first_image_reshaped, cmap='gray')
plt.title(f"Label: {first_label}")
plt.show()
```

</details>


## Jupyter Notebook Usage

```python
# In a Jupyter notebook cell
import nest_asyncio
nest_asyncio.apply()  # Required for Jupyter async support

from eclair.client import EclairClient

# Now you can use await directly in cells
client = EclairClient(server_url="http://localhost:3000")
result = await client.search_datasets("image classification")
datasets = result.structured_content['result']

# Display results in a nice format
from IPython.display import display, HTML
html_output = "<h3>Available Datasets</h3><ul>"
for dataset in datasets[:5]:
    html_output += f"<li><strong>{dataset['collection']}/{dataset['dataset']}</strong><br>"
    html_output += f"<a href='{dataset['url']}' target='_blank'>{dataset['url']}</a></li>"
html_output += "</ul>"
display(HTML(html_output))
```
