# Command Line Interface (CLI)

Eclair provides a powerful command-line interface for dataset discovery, downloading, and management. The CLI is perfect for automation, scripting, and quick dataset operations.

## Installation

The CLI is included with the Eclair package:

```bash
pip install eclair
```

Or for development:

```bash
pip install -e .
```

## Basic Usage

The main CLI command is `eclair-client`:

```bash
eclair-client --help
```

```
Usage: eclair-client [-h] [--server-url SERVER_URL] --tool TOOL [--query QUERY] [--collection COLLECTION] [--dataset DATASET] [--use-gemini] [--use-claude]

Eclair MCP Client

options:
  -h, --help            show this help message and exit
  --server-url SERVER_URL, -S SERVER_URL
                        MCP server URL
  --tool TOOL, -T TOOL  Tool to call
  --query QUERY, -Q QUERY
                        Query string for search-datasets
  --collection COLLECTION, -C COLLECTION
                        Dataset collection
  --dataset DATASET, -D DATASET
                        Dataset name
  --use-gemini, -G      Use Gemini client
  --use-claude, -L      Use Claude client
```

### Examples

```bash
# Test server connectivity
eclair-client --tool ping

# Search for datasets
eclair-client --tool search-datasets --query "mnist"

# Get croissant meta-data
eclair-client --tool search-datasets --query "mnist"
```

The reponses will be identical to the respective tools use in the [Python API](python-api.md). Check the Python docs for more detailes examples.


## Using AI models
You can also use Eclair with AI models directly from the command line. For this, you also need to set your AI model's API key and system prompt. For instance, for Gemini, do the following (replace XXX with your API key):

```bash
echo "GEMINI_API_KEY=XXX" >> .env
echo "GEMINI_SYSTEM_MD="src/eclair/client/gemini/gemini.md" >> .env
```

This also works with AI model integrations, e.g. with the `use-gemini` argument:
```bash
# Use with Gemini
eclair-client --use-gemini --tool ask --query "Find datasets for image segmentation"

# Short form
eclair-client -G -T ask -Q "Find datasets for image segmentation"
```

> TODO: The CLI interface currently doesn't keep a conversation state between commands. Use the IDE integrations and AI agents below for longer conversations with memory.

## CLI Reference Summary

| Method | Purpose | Returns |
|--------|---------|---------|
| `ping()` | Test server connectivity | "pong" if server is responsive |
| `search-datasets --query QUERY` | Search for datasets | List of matching datasets |
| `download-dataset --collection COLLECTION --dataset DATASET` | Download a dataset | Success/failure status |
| `serve-croissant --collection COLLECTION --dataset DATASET` | Get dataset metadata | Croissant JSON metadata |
| `datasets-preview-url --collection COLLECTION --dataset DATASET` | Get dataset preview URL | URL string for preview |
| `help` | Get server help information | Help text and usage info |

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
```
Of course! I'd be happy to help you find interesting datasets for image segmentation. Let's get started right away.

First, I'll search for datasets related to "image segmentation" on the eclair server. Then, I'll analyze their metadata to determine their size and present them to you in descending order.

Excellent! The search returned a great list of potential datasets. Now, I will retrieve the Croissant metadata for each of these to find their sizes and other relevant details. This might take a moment as I need to query each one individually.

Fantastic! I've successfully retrieved the metadata and extracted the sizes for each dataset. Here is the list of image segmentation datasets, ordered from largest to smallest:

1.  **`segments/sam-1b`**
    *   **Size**: 12.3 TB
    *   **Description**: The Segment Anything 1-Billion mask dataset (SA-1B). A massive, high-quality dataset with over 1 billion masks on 11 million images, designed for developing foundational models in computer vision.

2.  **`google/cityscapes`**
    *   **Size**: ~11.2 GB (11.0 GB + 241.0 MB)
    *   **Description**: A large-scale dataset focusing on semantic understanding of urban street scenes from 50 different cities. It's a standard benchmark for autonomous driving applications.

3.  **`segments/sidewalk-semantic`**
    *   **Size**: 1.8 GB
    *   **Description**: A collection of images focused on urban sidewalks with detailed semantic segmentation. Crucial for applications like autonomous robot navigation and accessibility tools.

4.  **`scene_parse_150`**
    *   **Size**: 1.0 GB
    *   **Description**: A benchmark for scene parsing, providing densely annotated images with pixel-level labels for a wide range of objects and scenes.

5.  **`augmented-traffic-signs`**
    *   **Size**: 1.0 GB
    *   **Description**: Contains 1000 images of traffic signs (1280x720) with segmentation masks, split into training and test sets.

6.  **`facebook/ade20k`**
    *   **Size**: 887.0 MB
    *   **Description**: A large-scale scene parsing benchmark with a diverse set of images and dense annotations for objects and their parts.

7.  **`nielsr/ade20k-panoptic`**
    *   **Size**: 887.0 MB
    *   **Description**: A panoptic version of the ADE20K dataset, providing annotations for both semantic "stuff" (like sky, road) and instance "things" (like individual cars, people).

8.  **`kvasir-v2`**
    *   **Size**: 495.0 MB
    *   **Description**: A diverse dataset of medical images from the gastrointestinal tract, annotated by experts for developing computer-aided diagnosis systems.

9.  **`kvasir-instrument`**
    *   **Size**: 80.0 MB
    *   **Description**: A dataset of images from colonoscopy procedures, with segmentation masks for various medical instruments. Useful for computer-assisted surgery applications.

10. **`fashion-mnist`**
    *   **Size**: 31.0 MB
    *   **Description**: A dataset of 70,000 28x28 grayscale images of clothing items. While primarily for classification, it can be used for simple segmentation tasks.

This list should give you a great starting point! The `sam-1b` dataset is exceptionally large and state-of-the-art, while `cityscapes` and `ade20k` are very popular and well-established benchmarks.
```
</details>

Eclair can be integrated in many more ways. Let us know your ideas!
