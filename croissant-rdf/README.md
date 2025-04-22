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


`croissant-rdf` is a Python tool that generates RDF (Resource Description Framework) data from datasets available on Hugging Face. This tool enables researchers and developers to convert data into a machine-readable format for enhanced querying and data analysis.

This is made possible due to an effort to align to the [MLCommons Croissant](https://github.com/mlcommons/croissant) schema, which HF and others conform to.

## Features

- Fetch datasets from HuggingFace or Kaggle.
- Convert datasets metadata to RDF format.
- Generate Turtle (`.ttl`) files for easy integration with SPARQL endpoints.

## Installation

croissant-rdf is available in PyPi!

```bash
pip install croissant-rdf
```

## Usage

After installing the package, you can use the command-line interface (CLI) to generate RDF data:

```sh
export HF_API_KEY={YOUR_KEY}
huggingface-rdf --fname huggingface.ttl --limit 10
```

Check out the `qlever_scripts` directory to get help loading the RDF into qlever for querying.

You can also easily use Jena fuseki and load the generated .ttl file from the Fuseki ui.

```sh
docker run -it -p 3030:3030 stain/jena-fuseki
```
### Extracting data from Kaggle
You'll need to get a Kaggle API key and it comes in a file called `kaggle.json`, you have to put the username and key into environment variables.

```sh
export KAGGLE_USERNAME={YOUR_USERNAME}
export KAGGLE_KEY={YOUR_KEY}
kaggle-rdf --fname kaggle.ttl --limit 10

# Optionally you can provide a positional argument to filter the dataset search
kaggle-rdf --fname kaggle.ttl --limit 10 covid
```

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

## Useful SPARQL Queries

SPARQL (SPARQL Protocol and RDF Query Language) is a query language used to retrieve and manipulate data stored in RDF (Resource Description Framework) format, typically within a triplestore. Here are a few useful SPARQL query examples you can try to implement on https://huggingface.co/spaces/david4096/huggingface-rdf

The basic structure of a SPQRQL query is SELECT: which you have to include a keywords that you would like to return in the result.
WHERE: Defines the triple pattern we want to match in the RDF dataset.

1. This query is used to retrieve distinct predicates from an Huggingface RDF dataset

```sparql
SELECT DISTINCT ?b WHERE {?a ?b ?c}
```

2. To retrieve information about a dataset, including its name, predicates, and the count of objects associated with each predicate. Includes a filters in the results to include only resources that are of type <https://schema.org/Dataset>.

```sparql
PREFIX schema: <https://schema.org/>
SELECT ?name ?p (count(?o) as ?predicate_count)
WHERE {
    ?dataset a schema:Dataset ;
        schema:name ?name ;
        ?p ?o .
}
GROUP BY ?p ?dataset
```

3. To retrieve distinct values with the keyword "bio" associated with the property <https://schema.org/keywords> regardless of the case.

```sparql
PREFIX schema: <https://schema.org/>
SELECT DISTINCT ?keyword
WHERE {
    ?s schema:keywords ?keyword .
    FILTER(CONTAINS(LCASE(?keyword), "bio"))
}
```

4. To retrieve distinct values for croissant columns associated with the predicate.

```sparql
PREFIX cr: <http://mlcommons.org/croissant/>
SELECT DISTINCT ?column
WHERE {
  	?s cr:column ?column
}
```

5. To retrieves the names of creators and the count of items they are associated with.

```sparql
PREFIX schema: <https://schema.org/>
SELECT ?creatorName (COUNT(?a) AS ?count)
WHERE {
    ?s schema:creator ?creator .
    ?creator schema:name ?creatorName .
}
GROUP BY ?creatorName
ORDER BY DESC(?count)
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

Run for HuggingFace:

```sh
uv run --env-file .env huggingface-rdf --fname huggingface.ttl --limit 10 covid
```

Run for kaggle:

```sh
uv run --env-file .env kaggle-rdf --fname kaggle.ttl --limit 10 covid
```

Run tests:

```sh
uv run pytest
```

> Test with HTML coverage report:
>
> ```sh
> uv run pytest --cov-report html && uv run python -m http.server 3000 --directory ./htmlcov
> ```

Run formatting and linting:

```sh
uvx ruff format && uvx ruff check --fix
```

Start a SPARQL endpoint on the generated files using [`rdflib-endpoint`](https://github.com/vemonet/rdflib-endpoint):

```sh
uv run rdflib-endpoint serve --store Oxigraph *.ttl
```

