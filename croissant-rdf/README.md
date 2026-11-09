# 🥐 croissant-rdf

[![PyPI - Version](https://img.shields.io/pypi/v/croissant-rdf.svg?logo=pypi&label=PyPI&logoColor=silver)](https://pypi.org/project/croissant-rdf/)
[![Tests](https://github.com/david4096/croissant-rdf/actions/workflows/test.yml/badge.svg)](https://github.com/david4096/croissant-rdf/actions/workflows/test.yml)

A proud [Biohackathon](http://www.biohackathon.org/) project 🧑‍💻🧬👩‍💻

* [Bridging Machine Learning and Semantic Web: A Case Study on Converting Hugging Face Metadata to RDF](https://osf.io/preprints/biohackrxiv/msv7x_v1)
* (In progress) Preprint from Elixir Biohackathon

<a target="_blank" href="https://colab.research.google.com/github/david4096/croissant-rdf/blob/main/example.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

[![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm-dark.svg)](https://huggingface.co/spaces/david4096/huggingface-rdf)

![image](https://github.com/user-attachments/assets/444fe9e9-0838-4f67-be7b-0f22a0789817)


`croissant-rdf` is a Python tool that generates RDF (Resource Description Framework) data from dataset metadata available across multiple ML platforms. This tool enables researchers and developers to create unified knowledge graphs from machine learning dataset metadata for enhanced querying, analysis, and semantic integration.

This is made possible due to an effort to align to the [MLCommons Croissant](https://github.com/mlcommons/croissant) schema, which multiple platforms (HuggingFace, Kaggle, OpenML, Dataverse) conform to.

## Features

- **Multi-provider support**: Fetch datasets from HuggingFace, Kaggle, OpenML, and Dataverse
- **RDF generation**: Convert Croissant metadata to RDF/Turtle format
- **Round-trip conversion**: Convert RDF back to JSON-LD format
- **Knowledge graph merging**: Combine RDF from multiple providers into unified graphs
- **Multiple output formats**: Support for Turtle, N-Triples, RDF/XML, JSON-LD, and N3
- **SPARQL-ready**: Generate files optimized for SPARQL endpoints

## Installation

croissant-rdf is available in PyPi!

```bash
pip install croissant-rdf
```

## Quick Start

### Generating RDF from Different Providers

**HuggingFace:**
```sh
export HF_API_KEY={YOUR_KEY}
huggingface-rdf --fname huggingface.ttl --limit 10

# With search filter
huggingface-rdf --fname huggingface.ttl --limit 10 covid
```

**Kaggle:**
```sh
export KAGGLE_USERNAME={YOUR_USERNAME}
export KAGGLE_KEY={YOUR_KEY}
kaggle-rdf --fname kaggle.ttl --limit 10

# With search filter
kaggle-rdf --fname kaggle.ttl --limit 10 covid
```

**OpenML:**
```sh
openml-rdf --fname openml.ttl --limit 10

# With search filter
openml-rdf --fname openml.ttl --limit 10 iris
```

**Dataverse:**
```sh
dataverse-rdf --fname dataverse.ttl --limit 10

# With search query
dataverse-rdf --fname dataverse.ttl --limit 10 soil
```

### Converting RDF to JSON-LD

Convert any RDF file back to Croissant JSON-LD format:

```sh
croissant-rdf to-jsonld my-datasets.ttl
# Creates: my-datasets.jsonld

# Specify output file
croissant-rdf to-jsonld my-datasets.ttl --output croissant.jsonld
```

### Merging Multiple RDF Sources

Combine RDF files from different providers into a unified knowledge graph:

```sh
# Merge specific files
croissant-rdf merge huggingface.ttl kaggle.ttl openml.ttl --output unified-kg.ttl

# Use wildcards to merge all TTL files
croissant-rdf merge *.ttl --output complete-kg.ttl

# Output in different format
croissant-rdf merge *.ttl --output kg.jsonld --format json-ld
```

### Querying with SPARQL

Load the generated RDF into a SPARQL endpoint:

**Using rdflib-endpoint:**
```sh
uv run rdflib-endpoint serve --store Oxigraph *.ttl
```

**Using Jena Fuseki:**
```sh
docker run -it -p 3030:3030 stain/jena-fuseki
# Then upload your .ttl file through the Fuseki web UI at http://localhost:3030
```

Check out the `qlever_scripts` directory for help loading RDF into QLever for high-performance querying.

### Running via Docker

You can use the `huggingface-rdf` or `kaggle-rdf` tools via Docker:

```bash
docker run -t -v $(pwd):/app david4096/croissant-rdf huggingface-rdf --fname docker.ttl
```

This will create a Turtle file `docker.ttl` in the current working directory.

### Using Common Workflow Language (CWL)

First install [cwltool](https://www.commonwl.org/user_guide/introduction/prerequisites.html) and then you can run the workflow using:

```bash
cwltool https://raw.githubusercontent.com/david4096/croissant-rdf/refs/heads/main/workflows/huggingface-rdf.cwl --fname cwl.ttl --limit 5
```

This will output a Turtle file called `cwl.ttl` in your local directory.

### Using Docker to run a Jupyter server
To launch a jupyter notebook server to run and develop on the project locally run the following:

Build:

```sh
docker build -t croissant-rdf-jupyter -f notebooks/Dockerfile .
```

Run Jupyter:

```sh
docker run -p 8888:8888 -v $(pwd):/app croissant-rdf-jupyter
```
The run command works for mac and linux for windows in PowerShell you need to use the following:
```sh
docker run -p 8888:8888 -v ${PWD}:/app croissant-rdf-jupyter
```

After that, you can access the Jupyter notebook server at http://localhost:8888.

## Example SPARQL Queries

SPARQL (SPARQL Protocol and RDF Query Language) is used to query RDF data. Try these examples on the [live demo](https://huggingface.co/spaces/david4096/huggingface-rdf) or your local SPARQL endpoint.

**1. List all predicates in the graph:**
```sparql
SELECT DISTINCT ?predicate
WHERE { ?s ?predicate ?o }
```

**2. Get dataset counts and properties:**
```sparql
PREFIX schema: <https://schema.org/>
SELECT ?name ?p (COUNT(?o) as ?predicate_count)
WHERE {
    ?dataset a schema:Dataset ;
        schema:name ?name ;
        ?p ?o .
}
GROUP BY ?name ?p
ORDER BY DESC(?predicate_count)
```

**3. Search datasets by keyword:**
```sparql
PREFIX schema: <https://schema.org/>
SELECT DISTINCT ?dataset ?name ?keyword
WHERE {
    ?dataset a schema:Dataset ;
        schema:name ?name ;
        schema:keywords ?keyword .
    FILTER(CONTAINS(LCASE(?keyword), "bio"))
}
```

**4. Find all Croissant fields:**
```sparql
PREFIX cr: <http://mlcommons.org/croissant/>
SELECT DISTINCT ?recordset ?field
WHERE {
    ?recordset cr:field ?field
}
```

**5. Top dataset creators:**
```sparql
PREFIX schema: <https://schema.org/>
SELECT ?creatorName (COUNT(?dataset) AS ?dataset_count)
WHERE {
    ?dataset a schema:Dataset ;
        schema:creator ?creator .
    ?creator schema:name ?creatorName .
}
GROUP BY ?creatorName
ORDER BY DESC(?dataset_count)
LIMIT 10
```

**6. Cross-provider dataset discovery:**
```sparql
PREFIX schema: <https://schema.org/>
PREFIX cr: <http://mlcommons.org/croissant/>
SELECT ?dataset ?name ?license ?recordset
WHERE {
    ?dataset a schema:Dataset ;
        schema:name ?name ;
        schema:license ?license .
    OPTIONAL { ?dataset schema:distribution/cr:containsRecordSet ?recordset }
}
LIMIT 100
```

## CLI Tools Reference

### Unified CLI

The `croissant-rdf` command provides a unified interface with subcommands:

```sh
croissant-rdf --help
croissant-rdf to-jsonld --help
croissant-rdf merge --help
```

| Subcommand | Description |
|------------|-------------|
| `croissant-rdf to-jsonld` | Convert RDF files back to Croissant JSON-LD |
| `croissant-rdf merge` | Merge multiple RDF files into a unified knowledge graph |

### Provider-Specific Tools

| Command | Description |
|---------|-------------|
| `huggingface-rdf` | Generate RDF from HuggingFace datasets |
| `kaggle-rdf` | Generate RDF from Kaggle datasets |
| `openml-rdf` | Generate RDF from OpenML datasets |
| `dataverse-rdf` | Generate RDF from Dataverse repositories |

All tools support `--help` for detailed usage information.

### Common Options

- `--fname`: Output file name (default: `croissant_metadata.ttl`)
- `--limit`: Maximum number of datasets to fetch (default: 10)
- `--format`: Output format: `turtle`, `n3`, `nt`, `xml`, `json-ld` (default: `turtle`)
- `--base`: Base URL for RDF resources (default: `https://w3id.org/croissant-rdf/data/`)

## Use Cases

### Building a Cross-Platform Dataset Catalog

```sh
# Collect metadata from different sources
huggingface-rdf --fname hf.ttl --limit 100 nlp
kaggle-rdf --fname kaggle.ttl --limit 100 nlp
openml-rdf --fname openml.ttl --limit 100

# Merge into unified catalog
croissant-rdf merge hf.ttl kaggle.ttl openml.ttl --output nlp-catalog.ttl

# Query the unified catalog
uv run rdflib-endpoint serve --store Oxigraph nlp-catalog.ttl
```

### Creating Bioinformatics Dataset Knowledge Graph

```sh
# Gather bioinformatics datasets
huggingface-rdf --fname bio-hf.ttl --limit 200 bioinformatics
openml-rdf --fname bio-openml.ttl --limit 50 genome
dataverse-rdf --fname bio-dataverse.ttl --limit 50 biology

# Create unified knowledge graph
croissant-rdf merge bio-*.ttl --output bioinformatics-kg.ttl
```

### Dataset Metadata Analysis

```sh
# Export to JSON-LD for analysis
croissant-rdf to-jsonld my-datasets.ttl

# Process with Python
python -c "
import json
with open('my-datasets.jsonld') as f:
    data = json.load(f)
    print(f'Found {len(data)} resources')
"
```

## Contributing

We welcome contributions! Please open an issue or submit a pull request!

### Development

> We recommend to use [`uv`](https://docs.astral.sh/uv/getting-started/installation/) for working in development, it will handle virtual environments and dependencies automatically and really quickly.

Create a `.env` file with the required API keys.

```sh
HF_API_KEY=hf_YYY
KAGGLE_USERNAME=you
KAGGLE_KEY=0000
```

**Run data harvesters:**

```sh
# HuggingFace
uv run --env-file .env huggingface-rdf --fname huggingface.ttl --limit 10 covid

# Kaggle
uv run --env-file .env kaggle-rdf --fname kaggle.ttl --limit 10 covid

# OpenML (no API key needed)
uv run openml-rdf --fname openml.ttl --limit 10

# Dataverse
uv run dataverse-rdf --fname dataverse.ttl --limit 10
```

**Run tests:**

```sh
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_merge_rdf.py -v

# With coverage report
uv run pytest --cov-report html
uv run python -m http.server 3000 --directory ./htmlcov
```

**Code quality:**

```sh
# Format code
uvx ruff format

# Lint and fix
uvx ruff check --fix
```

**Local SPARQL endpoint:**

```sh
uv run rdflib-endpoint serve --store Oxigraph *.ttl
```

## Architecture

```
croissant-rdf/
├── src/croissant_rdf/
│   ├── _src/
│   │   ├── croissant_harvester.py    # Abstract base class
│   │   ├── providers/                # Provider implementations
│   │   │   ├── huggingface.py
│   │   │   ├── kaggle.py
│   │   │   ├── openml.py
│   │   │   └── dataverse.py
│   │   ├── cli.py                   # Unified CLI with subcommands
│   │   ├── rdf_to_jsonld.py         # RDF → JSON-LD conversion
│   │   ├── merge_rdf.py             # Multi-file RDF merging
│   │   └── utils.py                 # Shared utilities
│   └── providers/                   # CLI entry points
├── tests/                           # Test suite
└── notebooks/                       # Jupyter examples
```

