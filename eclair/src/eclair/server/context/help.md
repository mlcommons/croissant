# Eclair Dataset MCP Server Help

This document outlines how to use the available MCP tools to interact with datasets through the Eclair server.

## Available Tools

The Eclair MCP Server provides the following tools for dataset discovery and management:

- `search-datasets` - Search for datasets using a query string
- `datasets-preview-url` - Get a download URL for a dataset preview
- `serve-croissant` - Get the Croissant dataset metadata
- `validate-croissant` - Validate Croissant metadata
- `download-dataset` - Get download information for a dataset
- `help` - Get this help information
- `ping` - Test server connectivity

## 1. Searching for Datasets

To find datasets based on keywords or topics:

1. **Use the `search-datasets` tool** with a query string relevant to the datasets you are looking for.
   - Example: Search for "images" or "image classification" to find computer vision datasets
2. **Review the results** - The tool returns a list of datasets matching your query, including names, descriptions, and other metadata.

**Tool:** `search-datasets`
**Parameters:** `query` (string) - Keywords to search for

## 2. Getting and Viewing a Dataset Preview

To get a preview of a specific dataset:

1. **Identify the dataset** - You need the `collection` name and `dataset` name from search results
2. **Get the preview download URL** using the `datasets-preview-url` tool
3. **Download the preview file** - The URL points to a Parquet format file containing a sample of the data
4. **View the data** - Load the downloaded `.parquet` file using pandas or similar tools:

```python
import pandas as pd
import requests
import io

# Get the preview URL using the MCP tool
# Then download and view:
response = requests.get(preview_url)
if response.status_code == 200:
    df = pd.read_parquet(io.BytesIO(response.content))
    print(df.head())
```

**Tool:** `datasets-preview-url`
**Parameters:** `collection` (string), `dataset` (string)

## 3. Reviewing Dataset Metadata

To examine the detailed Croissant metadata for a specific dataset:

1. **Identify the dataset** - You need the `collection` name and `dataset` name
2. **Request the metadata** using the `serve-croissant` tool
3. **Inspect the JSON-LD** - The tool returns Croissant metadata describing the dataset's structure, fields, distributions, and more

**Tool:** `serve-croissant`
**Parameters:** `collection` (string), `dataset` (string)

## 4. Validating Croissant Metadata

To validate Croissant metadata for compliance with the specification:

1. **Prepare your metadata** - Have your Croissant JSON-LD metadata ready
2. **Use the validation tool** - Pass the metadata to `validate-croissant`
3. **Review validation results** - The tool returns a validation report with any issues found

**Tool:** `validate-croissant`
**Parameters:** `metadata_json` (object) - The Croissant metadata to validate

## 5. Getting Dataset Download Information

To get information about downloading a complete dataset:

1. **Identify the dataset** - You need the `collection` name and `dataset` name
2. **Request download info** using the `download-dataset` tool
3. **Follow the provided instructions** - The tool returns download URLs and instructions

**Tool:** `download-dataset`
**Parameters:** `collection` (string), `dataset` (string)