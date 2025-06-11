# Croissant 🥐

[![CI](https://github.com/mlcommons/datasets_format/actions/workflows/ci.yml/badge.svg)](https://github.com/mlcommons/datasets_format/actions/workflows/ci.yml/badge.svg)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Summary

Croissant 🥐 is a high-level format for machine learning datasets that combines metadata, resource file descriptions, data structure, and default ML semantics into a single file; it works with existing datasets to make them easier to find, use, and support with tools. Croissant builds on <a href="https://schema.org/">schema.org</a>, and its Dataset vocabulary, a widely used format to represent datasets on the Web, and make them searchable. You can find a gentle introduction in the companion paper [Croissant: A Metadata Format for ML-Ready Datasets](https://doi.org/10.1145/3650203.3663326).

<img src='/docs/images/croissant-summary.png' width='500'>

## Trying It Out

Croissant is currently under development by the community. You can try the Croissant implementation, `mlcroissant`:

Installation (requires Python 3.10+):

```bash
pip install mlcroissant
```

Loading an example dataset:

```python3
import mlcroissant as mlc
ds = mlc.Dataset("https://raw.githubusercontent.com/mlcommons/croissant/main/datasets/1.0/gpt-3/metadata.json")
metadata = ds.metadata.to_json()
print(f"{metadata['name']}: {metadata['description']}")
for x in ds.records(record_set="default"):
    print(x)
```

Use it in your ML workflow:

```python3
# 1. Point to a local or remote Croissant file
import mlcroissant as mlc
url = "https://huggingface.co/api/datasets/fashion_mnist/croissant"
# 2. Inspect metadata
print(mlc.Dataset(url).metadata.to_json())
# 3. Use Croissant dataset in your ML workload
import tensorflow_datasets as tfds
builder = tfds.core.dataset_builders.CroissantBuilder(
    jsonld=url,
    record_set_ids=["record_set_fashion_mnist"],
    file_format='array_record',
)
builder.download_and_prepare()
# 4. Split for training/testing
train, test = builder.as_data_source(split=['default[:80%]', 'default[80%:]'])
```

Please see the [notebook recipes](python/mlcroissant/recipes) for more examples.

## Why a standard format for ML datasets?

Datasets are the source code of machine learning (ML), but working with ML datasets is needlessly hard because each dataset has a unique file organization and method for translating file contents into data structures and thus requires a novel approach to using the data. We need a standard dataset format to make it easier to find and use ML datasets and especially to develop tools for creating, understanding, and improving ML datasets.

## The Croissant Format

Croissant 🥐 is a high-level format for machine learning datasets. Croissant brings together four rich layers (in a tasty manner, we hope 😉):

- Metadata: description of the dataset, including responsible ML aspects
- Resources: one or more files or other sources containing the raw data
- Structure: how the raw data is combined and arranged into data structures for use
- ML semantics: how the data is most often used in an ML context

## Simple Format Example

Here is an extremely simple example of the Croissant format, with comments showing the four layers. The `@context` preamble is not included for simplicity. Complete croissant definitions for a wide range of datasets are included in the `datasets` folder of this repository.

```json
{
  "@type": "sc:Dataset",
  "name": "minimal_example_with_recommended_fields",
  "description": "This is a minimal example, including the required and the recommended fields.",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "url": "https://example.com/dataset/recipes/minimal-recommended",
  "conformsTo": "http://mlcommons.org/croissant/1.0",
  "distribution": [
    {
      "@type": "cr:FileObject",
      "@id": "minimal.csv",
      "name": "minimal.csv",
      "contentUrl": "data/minimal.csv",
      "encodingFormat": "text/csv",
      "sha256": "48a7c257f3c90b2a3e529ddd2cca8f4f1bd8e49ed244ef53927649504ac55354"
    }
  ],
  "recordSet": [
    {
      "@type": "cr:RecordSet",
      "name": "examples",
      "description": "Records extracted from the example table, with their schema.",
      "field": [
        {
          "@type": "cr:Field",
          "name": "name",
          "description": "The first column contains the name.",
          "dataType": "sc:Text",
          "source": {
            "fileObject": { "@id": "minimal.csv" },
            "extract": {
              "column": "name"
            }
          }
        },
        {
          "@type": "cr:Field",
          "name": "age",
          "description": "The second column contains the age.",
          "dataType": "sc:Integer",
          "source": {
            "fileObject": { "@id": "minimal.csv" },
            "extract": {
              "column": "age"
            }
          }
        }
      ]
    }
  ]
}
```

## Resources

- [Github Repo](https://github.com/mlcommons/croissant)
  - Specification
  - Examples
  - Verifier
- [Shared Drive](https://drive.google.com/corp/drive/folders/1StGRO4CGWUsX9kHdM5aOQNOF1L5e2y97)
  - Requirements Document
  - Responsible AI Approach

<!---
## How to use
* Downloading an ML dataset: Look for a Croissant file. If it doesn’t exist, ask the dataset owners for one and point them to this page.
* Loading an ML dataset for use with a model: pyTorch and TensorFlow integrations enable loading any dataset with a Croissant file and recognized data file types as follows:
* Creating or sharing an ML dataset: Create a Croissant file for your dataset starting with one of the templates here and verifying correctness using this script.
* Developing ML dataset tooling: Consider supporting Croissant as part of your tool. You can find generic loader code here (under development).
* Accepting ML dataset papers: Consider requiring Croissant files for new datasets. Help everyone by making datasets easier to find and use!
-->

## Getting involved

- [Join](https://mlcommons.org/community/subscribe/) the mailing list
- Attend Croissant meetings (please joint the list to automatically receive the invite)
- [File issues for](https://github.com/mlcommons/croissant) bugs for feature requests
- [Contribute to the code](https://github.com/mlcommons/croissant). To merge PRs, you will need to sign the MLCommons Association CLA at: https://mlcommons.org/community/subscribe/

## Integrations

- [Datasets Search](https://datasetsearch.research.google.com) crawls and indexes Croissant JSON-LD files on the web and provides a filter to restrict results to Croissant datasets.
- [Kaggle](https://www.kaggle.com/datasets) embeds Croissant JSON-LD directly in their HTML, and also provides the following ways to download the Croissant JSON-LD file:
  - Via an `Export metadata as Croissant` button on the dataset's page (ex: <https://www.kaggle.com/datasets/unsdsn/world-happiness>)
  - Via download URL (ex: <https://www.kaggle.com/datasets/unsdsn/world-happiness/croissant/download>)
- [OpenML](https://www.openml.org/search?type=data) offers a `Croissant` button on all of their datasets to download the underlying Croissant JSON-LD file.
- [Hugging Face](https://huggingface.co/) embeds Croissant JSON-LD directly in the HTML of dataset pages. It also offers ways to download the Croissant JSON-LD file:
  - Via a `Croissant` tag button on the dataset's page (ex: <https://huggingface.co/datasets/CohereForAI/aya_collection>)
  - Via their API (ex: <https://huggingface.co/api/datasets/CohereForAI/aya_collection/croissant>)
- [TFDS](https://www.tensorflow.org/datasets/overview) has a [`CroissantBuilder`](https://www.tensorflow.org/datasets/format_specific_dataset_builders#croissantbuilder) to transform any JSON-LD file into a TFDS dataset, which makes it possible to load the data into TensorFlow, JAX and PyTorch.
- [CKAN](https://ckan.org) supports Croissant through the [ckanext-dcat](https://github.com/ckan/ckanext-dcat) extension starting from version 2.3.0. The metadata is embedded in the dataset's page source and is also accessible through a dedicated endpoint. For datasets imported into the CKAN DataStore, the resources will expose Croissant's RecordSet objects, detailing data fields like column names and types.
- [Dataverse](https://dataverse.org) offers an [addon](https://github.com/gdcc/exporter-croissant) to export datasets in Croissant format and embed Croissant directly in the HTML of dataset landing pages.

## Licensing

Croissant project code and examples are licensed under Apache 2.

## Governance

Croissant is being developed by the community as a Task Force of the [MLCommons Association](http://mlcommons.org) Datasets Working Group.
The Task Force is open to anyone (as is the parent [Datasets working group](https://mlcommons.org/en/groups/datasets/)).
The Task Force is co-chaired by [Omar Benjelloun](mailto:benjello@google.com) and [Elena Simperl](mailto:elena.simperl@kcl.ac.uk).

## Contributors

Albert Villanova (Hugging Face), Andrew Zaldivar (Google), Baishan Guo (Meta), Carole Jean-Wu (Meta), Ce Zhang (ETH Zurich), Costanza Conforti (Google), D. Sculley (Kaggle), Dan Brickley (Schema.Org), Eduardo Arino de la Rubia (Meta), Edward Lockhart (Deepmind), Elena Simperl (King's College London), Goeff Thomas (Kaggle), Joan Giner-Miguelez (UOC), Joaquin Vanschoren (TU/Eindhoven, OpenML), Jos van der Velde (TU/Eindhoven, OpenML), Julien Chaumond (Hugging Face), Kurt Bollacker (MLCommons), Lora Aroyo (Google), Luis Oala (Dotphoton), Meg Risdal (Kaggle), Natasha Noy (Google), Newsha Ardalani (Meta), Omar Benjelloun (Google), Peter Mattson (MLCommons), Pierre Marcenac (Google), Pierre Ruyssen (Google), Pieter Gijsbers (TU/Eindhoven, OpenML), Prabhant Singh (TU/Eindhoven, OpenML), Quentin Lhoest (Hugging Face), Steffen Vogler (Bayer), Taniya Das (TU/Eindhoven, OpenML), Michael Kuchnik (Meta)

Thank you for supporting Croissant! 🙂

## Citation

```
@inproceedings{NEURIPS2024_9547b09b,
 author = {Akhtar, Mubashara and Benjelloun, Omar and Conforti, Costanza and Foschini, Luca and Gijsbers, Pieter and Giner-Miguelez, Joan and Goswami, Sujata and Jain, Nitisha and Karamousadakis, Michalis and Krishna, Satyapriya and Kuchnik, Michael and Lesage, Sylvain and Lhoest, Quentin and Marcenac, Pierre and Maskey, Manil and Mattson, Peter and Oala, Luis and Oderinwale, Hamidah and Ruyssen, Pierre and Santos, Tim and Shinde, Rajat and Simperl, Elena and Suresh, Arjun and Thomas, Goeffry and Tykhonov, Slava and Vanschoren, Joaquin and Varma, Susheel and van der Velde, Jos and Vogler, Steffen and Wu, Carole-Jean and Zhang, Luyao},
 booktitle = {Advances in Neural Information Processing Systems},
 editor = {A. Globerson and L. Mackey and D. Belgrave and A. Fan and U. Paquet and J. Tomczak and C. Zhang},
 pages = {82133--82148},
 publisher = {Curran Associates, Inc.},
 title = {Croissant: A Metadata Format for ML-Ready Datasets},
 url = {https://proceedings.neurips.cc/paper_files/paper/2024/file/9547b09b722f2948ff3ddb5d86002bc0-Paper-Datasets_and_Benchmarks_Track.pdf},
 volume = {37},
 year = {2024}
}
```
