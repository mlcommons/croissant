# API Reference

Eclair provides several APIs and tools for dataset discovery and management. This reference covers all available interfaces including MCP tools, REST API, and Python SDK.

## Model Context Protocol (MCP) Tools

Eclair implements the Model Context Protocol, providing standardized tools for AI agents to discover and work with datasets.

### Available Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `search-datasets` | Search for datasets using natural language | `query` (required) |
| `download-dataset` | Download a dataset to local storage | `collection`, `dataset` (both required) |
| `datasets-preview-url` | Get preview URL for dataset samples | `collection`, `dataset` (both required) |
| `serve-croissant` | Get Croissant metadata for a dataset | `collection`, `dataset` (both required) |
| `validate-croissant` | Validate Croissant metadata | `metadata_json` (required) |
| `help` | Get help information | No parameters |
| `ping` | Test server connectivity | No parameters |

### Tool Schemas

#### search-datasets

Search for datasets using natural language queries.

```json
{
  "name": "search-datasets",
  "description": "Search for datasets using a query string",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "title": "Query",
        "description": "Search query for finding datasets"
      }
    },
    "required": ["query"]
  }
}
```

**Example Usage:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "search-datasets", 
    "arguments": {
      "query": "Fashion-MNIST"
    }
  }
}
```

**Response (Sample):**
```json
{
  "result": [
    {
      "document": {
        "collection_name": "Han-Xiao",
        "entity_name": "Fashion-MNIST", 
        "entity_type": "dataset",
        "full_name": "dataset/Han-Xiao/Fashion-MNIST",
        "metadata": {
          "__type": "sc:Dataset",
          "conformsTo": "http://mlcommons.org/croissant/1.0",
          "name": "Fashion-MNIST",
          "description": "Fashion-MNIST is a dataset of Zalando's article images, consisting of a training set of 60,000 examples and a test set of 10,000 examples...",
          "url": "https://www.openml.org/search?type=data&id=40996",
          "license": "Public"
        }
      },
      "highlight": {
        "metadata": {
          "description": {
            "matched_tokens": ["Fashion-MNIST"], 
            "snippet": "<mark>Fashion-MNIST</mark> is a dataset of Zalando's article images"
          }
        }
      },
      "text_match": 1157451471441100800,
      "text_match_info": {
        "best_field_score": "2211897868288",
        "best_field_weight": 15,
        "fields_matched": 2,
        "score": "1157451471441100922",
        "tokens_matched": 1
      }
    }
  ]
}
```

#### download-dataset

Download a dataset to local storage.

```json
{
  "name": "download-dataset",
  "description": "Download a dataset",
  "inputSchema": {
    "type": "object",
    "properties": {
      "collection": {
        "type": "string",
        "title": "Collection",
        "description": "Dataset collection name"
      },
      "dataset": {
        "type": "string", 
        "title": "Dataset",
        "description": "Dataset identifier"
      }
    },
    "required": ["collection", "dataset"]
  }
}
```

**Example Usage:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "download-dataset",
    "arguments": {
      "collection": "Han-Xiao",
      "dataset": "Fashion-MNIST"
    }
  }
}
```

**Response:**
```json
{
  "result": {
    "metadata": {
      "url": "https://www.openml.org/search?type=data&id=40996",
      "name": "Fashion-MNIST",
      "@type": "sc:Dataset",
      "sameAs": "https://github.com/zalandoresearch/fashion-mnist",
      "creator": {
        "url": "https://huggingface.co/Han-Xiao",
        "name": "Han-Xiao",
        "@type": "sc:Organization"
      },
      "license": "Public",
      "conformsTo": "http://mlcommons.org/croissant/1.0",
      "description": "Fashion-MNIST is a dataset of Zalando's article images..."
    },
    "asset_origin": "openml",
    "data_path": "Han-Xiao/Fashion-MNIST",
    "instructions": "# Install if necessary\n# !pip install datasets pandas\n\nfrom datasets import load_dataset\nimport pandas as pd\n\n# 1. Load Fashion-MNIST dataset from OpenML\ndataset = load_dataset(\"Han-Xiao/Fashion-MNIST\")\n\n# The dataset has different splits (train, test)\nprint(dataset)\n\n# 2. Take a look at a few examples\nprint(\"\\nFirst few training examples:\")\nprint(dataset[\"train\"].select(range(5)))\n\n# 3. Convert to a pandas DataFrame for easier exploration\ndf_train = pd.DataFrame(dataset[\"train\"])\n\nprint(\"\\nPandas DataFrame Head:\")\nprint(df_train.head())\n\n# 4. Simple exploration\nprint(\"\\nBasic info:\")\nprint(df_train.info())"
  }
}
```

#### datasets-preview-url

Get a URL for previewing dataset samples.

```json
{
  "name": "datasets-preview-url",
  "description": "Get a download url for a dataset preview",
  "inputSchema": {
    "type": "object",
    "properties": {
      "collection": {
        "type": "string",
        "title": "Collection"
      },
      "dataset": {
        "type": "string",
        "title": "Dataset" 
      }
    },
    "required": ["collection", "dataset"]
  }
}
```

**Example Usage:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "datasets-preview-url",
    "arguments": {
      "collection": "Han-Xiao",
      "dataset": "Fashion-MNIST"
    }
  }
}
```

**Response:**
```json
{
  "result": "https://dock.jetty.io/api/v1/datasets/Han-Xiao/Fashion-MNIST/preview"
}
```

#### serve-croissant

Get Croissant metadata for a dataset.

```json
{
  "name": "serve-croissant",
  "description": "Get the Croissant dataset metadata",
  "inputSchema": {
    "type": "object",
    "properties": {
      "collection": {
        "type": "string",
        "title": "Collection"
      },
      "dataset": {
        "type": "string",
        "title": "Dataset"
      }
    },
    "required": ["collection", "dataset"]  
  }
}
```

**Example Usage:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "serve-croissant",
    "arguments": {
      "collection": "Han-Xiao",
      "dataset": "Fashion-MNIST"
    }
  }
}
```

**Response (Sample):**
```json
{
  "result": {
    "url": "https://www.openml.org/search?type=data&id=40996",
    "name": "Fashion-MNIST",
    "@type": "sc:Dataset",
    "sameAs": "https://github.com/zalandoresearch/fashion-mnist",
    "creator": {
      "url": "https://huggingface.co/Han-Xiao",
      "name": "Han-Xiao",
      "@type": "sc:Organization"
    },
    "license": "Public",
    "@context": {
      "cr": "http://mlcommons.org/croissant/",
      "sc": "https://schema.org/",
      "@vocab": "https://schema.org/"
    },
    "keywords": [
      "image-classification",
      "multi-class-image-classification",
      "expert-generated",
      "English",
      "Public",
      "10K - 100K",
      "Fashion-MNIST"
    ],
    "conformsTo": "http://mlcommons.org/croissant/1.0",
    "description": "Fashion-MNIST is a dataset of Zalando's article images—consisting of a training set of 60,000 examples and a test set of 10,000 examples...",
    "recordSet": [
      {
        "@id": "fashion_mnist",
        "name": "Fashion-MNIST",
        "@type": "cr:RecordSet",
        "field": [
          {
            "@id": "fashion_mnist/image",
            "name": "fashion_mnist/image",
            "@type": "cr:Field",
            "dataType": "sc:ImageObject",
            "description": "28x28 grayscale image of fashion item."
          },
          {
            "@id": "fashion_mnist/label",
            "name": "fashion_mnist/label", 
            "@type": "cr:Field",
            "dataType": "sc:Integer",
            "description": "Fashion item class label (0-9).\nLabels:\n0: T-shirt/top, 1: Trouser, 2: Pullover, 3: Dress, 4: Coat, 5: Sandal, 6: Shirt, 7: Sneaker, 8: Bag, 9: Ankle boot"
          }
        ]
      }
    ],
    "distribution": [
      {
        "@id": "openml_repo",
        "name": "openml_repo",
        "@type": "cr:FileObject",
        "contentUrl": "https://www.openml.org/search?type=data&id=40996",
        "encodingFormat": "openml+arff"
      }
    ]
  }
}
```

#### validate-croissant

Validate Croissant metadata for compliance.

```json
{
  "name": "validate-croissant", 
  "description": "Validate a Croissant metadata file",
  "inputSchema": {
    "type": "object",
    "properties": {
      "metadata_json": {
        "type": "object",
        "title": "Metadata Json",
        "additionalProperties": true
      }
    },
    "required": ["metadata_json"]
  }
}
```

**Example Usage:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "validate-croissant",
    "arguments": {
      "metadata_json": {
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "contributor": {
          "name": ["Jock A. Blackard", "Dr. Denis J. Dean", "Dr. Charles W. Anderson"]
        },
        "dateCreated": "2014-04-23T13:14:37",
        "description": "**Covertype**\nPredicting forest cover type from cartographic variables only (no remotely sensed data)...",
        "distribution": [
          {
            "contentUrl": "https://data.openml.org/datasets/0000/0180/dataset_180.pq",
            "description": "Data file belonging to the dataset.",
            "encodingFormat": "application/x-parquet",
            "md5": "c741394174287c04331718c76be0336e",
            "name": "data-file"
          }
        ],
        "inLanguage": "en",
        "isAccessibleForFree": true,
        "keywords": ["Data Science", "Ecology", "Machine Learning", "study_10", "uci"],
        "license": "Public",
        "name": "covertype",
        "recordSet": [
          {
            "data": [
              {"enumerations/class/value": "Aspen"},
              {"enumerations/class/value": "Cottonwood_Willow"},
              {"enumerations/class/value": "Douglas_fir"},
              {"enumerations/class/value": "Krummholz"},
              {"enumerations/class/value": "Lodgepole_Pine"},
              {"enumerations/class/value": "Ponderosa_Pine"},
              {"enumerations/class/value": "Spruce_Fir"}
            ],
            "dataType": "sc:Enumeration",
            "description": "Possible values for class",
            "field": [
              {
                "dataType": "sc:Text",
                "description": "The value of class.",
                "name": "value"
              }
            ],
            "name": "class"
          }
        ],
        "url": "https://www.openml.org/d/180",
        "version": 1
      }
    }
  }
}
```

**Response:**
```json
{
  "result": {
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
        "message": "Record set 'enumerations/class' passed validation.",
        "status": "pass"
      }
    ]
  }
}
```

**Note**: The validation tool now successfully validates proper Croissant 1.0 metadata. This example uses the OpenML Covertype dataset with complete metadata structure including distribution, recordSet, and field definitions.

##### Validation with Incomplete Metadata

Some datasets may have schema-compliant but functionally incomplete metadata:

```json
{
  "method": "tools/call",
  "params": {
    "name": "validate-croissant",
    "arguments": {
      "metadata_json": {
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "name": "Fashion-MNIST",
        "description": "Fashion-MNIST dataset...",
        "recordSet": [
          {
            "name": "data-file-description",
            "description": "The fields are omitted, because this dataset has too many."
          }
        ],
        "distribution": [
          {
            "contentUrl": "https://data.openml.org/datasets/0004/40996/dataset_40996.pq",
            "encodingFormat": "application/x-parquet",
            "name": "data-file"
          }
        ]
      }
    }
  }
}
```

**Response:**
```json
{
  "result": {
    "valid": false,
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
        "passed": false,
        "message": "Record set failed due to generation error: TypeError: object of type 'NoneType' has no len()",
        "status": "warning"
      }
    ]
  }
}
```

This shows that metadata can be **schema-compliant** but **generation-incomplete** due to missing field definitions.

#### help

Get comprehensive help information.

```json
{
  "name": "help",
  "description": "Get help for the Eclair Dataset MCP server",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

**Example Usage:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "help",
    "arguments": {}
  }
}
```

**Response:**
```json
{
  "result": "# Eclair Dataset MCP Server\n\nEclair provides access to a curated collection of datasets for machine learning and data science.\n\n## Available Tools\n\n### search-datasets\nSearch for datasets using natural language queries.\n\nParameters:\n- query (string, required): Search query to find relevant datasets\n\nExample:\n```\nmcp_client.call(\"search-datasets\", {\"query\": \"computer vision\"})\n```\n\n### datasets-preview-url\nGet a preview URL for a specific dataset.\n\nParameters:\n- collection (string, required): Collection name (e.g., \"Han-Xiao\")\n- dataset (string, required): Dataset name (e.g., \"Fashion-MNIST\")\n\nExample:\n```\nmcp_client.call(\"datasets-preview-url\", {\"collection\": \"Han-Xiao\", \"dataset\": \"Fashion-MNIST\"})\n```\n\n### serve-croissant\nRetrieve Croissant metadata for a dataset.\n\nParameters:\n- collection (string, required): Collection name\n- dataset (string, required): Dataset name\n\nExample:\n```\nmcp_client.call(\"serve-croissant\", {\"collection\": \"Han-Xiao\", \"dataset\": \"Fashion-MNIST\"})\n```\n\n### validate-croissant\nValidate Croissant metadata for compliance.\n\nParameters:\n- metadata_json (object, required): Croissant metadata to validate\n\nExample:\n```\nmcp_client.call(\"validate-croissant\", {\"metadata_json\": croissant_metadata})\n```\n\n### download-dataset\nDownload a dataset with metadata and usage instructions.\n\nParameters:\n- collection (string, required): Collection name\n- dataset (string, required): Dataset name\n\nExample:\n```\nmcp_client.call(\"download-dataset\", {\"collection\": \"Han-Xiao\", \"dataset\": \"Fashion-MNIST\"})\n```\n\n### ping\nTest server connectivity.\n\nParameters: None\n\nExample:\n```\nmcp_client.call(\"ping\", {})\n```\n\n## Getting Started\n\n1. Search for datasets: `search-datasets`\n2. Preview dataset: `datasets-preview-url`  \n3. Get metadata: `serve-croissant`\n4. Download dataset: `download-dataset`\n\n## Support\n\nFor more information, visit: https://github.com/jvanscho/eclair"
}
```

#### ping

Test server connectivity and health.

```json
{
  "name": "ping",
  "description": "Test that the Eclair server is working", 
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

**Example Usage:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "ping",
    "arguments": {}
  }
}
```

**Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Pong! Eclair MCP Server is running successfully."
    }
  ]
}
```