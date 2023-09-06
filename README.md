# Croissant 🥐

[![CI](https://github.com/mlcommons/datasets_format/actions/workflows/ci.yml/badge.svg)](https://github.com/mlcommons/datasets_format/actions/workflows/ci.yml/badge.svg)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Summary

Croissant 🥐 is a high-level format for machine learning datasets that combines metadata, resource file descriptions, data structure, and default ML semantics into a single file; it works with existing datasets to make them easier to find, use, and support with tools.

Croissant builds on [schema.org](https://schema.org/), and its Dataset vocabulary, a widely used format to represent datasets on the Web, and make them searchable.

Croissant is currently under development by the community.

## Why a standard format for ML datasets?

Datasets are the source code of machine learning (ML), but working with ML datasets is needlessly hard because each dataset has a unique file organization and method for translating file contents into data structures and thus requires a novel approach to using the data. We need a standard dataset format to make it easier to find and use ML datasets and especially to develop tools for creating, understanding, and improving ML datasets.

## The Croissant Format

Croissant 🥐 is a high-level format for machine learning datasets. Croissant brings together four rich layers (in a tasty manner, we hope 😉):
* Metadata: description of the dataset, including responsible ML aspects
* Resources: one or more files or other sources containing the raw data
* Structure: how the raw data is combined and arranged into data structures for use
* ML semantics: how the data is most often used in an ML context

## Simple Example

Here is an extremely simple example of the croissant format, with comments showing the four layers:

```json
{
  "@type": "sc:Dataset",
  "name": "minimal_example_with_recommended_fields",
  "description": "This is a minimal example, including the required and the recommended fields.",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "url": "https://example.com/dataset/recipes/minimal-recommended",
  "distribution": [
    {
      "@type": "sc:FileObject",
      "name": "minimal.csv",
      "contentUrl": "data/minimal.csv",
      "encodingFormat": "text/csv",
      "sha256": "48a7c257f3c90b2a3e529ddd2cca8f4f1bd8e49ed244ef53927649504ac55354"
    }
  ],
  "recordSet": [
    {
      "@type": "ml:RecordSet",
      "name": "examples",
      "description": "Records extracted from the example table, with their schema.",
      "field": [
        {
          "@type": "ml:Field",
          "name": "name",
          "description": "The first column contains the name.",
          "dataType": "sc:Text",
          "references": {
            "dataExtraction": {
              "csvColumn": "name"
            },
            "distribution": "minimal.csv"
          }
        },
        {
          "@type": "ml:Field",
          "name": "age",
          "description": "The second column contains the age.",
          "dataType": "sc:Integer",
          "references": {
            "dataExtraction": {
              "csvColumn": "age"
            },
            "distribution": "minimal.csv"
          }
        }
      ]
    }
  ]
}
```

## Resources

* [Github Repo](https://github.com/mlcommons/croissant)
    * Specification
    * Examples
    * Verifier
* [Shared Drive](https://drive.google.com/corp/drive/folders/1StGRO4CGWUsX9kHdM5aOQNOF1L5e2y97)
    * Requirements Document
    * Responsible AI Approach	

<!---
## How to use
* Downloading an ML dataset: Look for a Croissant file. If it doesn’t exist, ask the dataset owners for one and point them to this page.
* Loading an ML dataset for use with a model: pyTorch and TensorFlow integrations enable loading any dataset with a Croissant file and recognized data file types as follows:
* Creating or sharing an ML dataset: Create a Croissant file for your dataset starting with one of the templates here and verifying correctness using this script.
* Developing ML dataset tooling: Consider supporting Croissant as part of your tool. You can find generic loader code here (under development).
* Accepting ML dataset papers: Consider requiring Croissant files for new datasets. Help everyone by making datasets easier to find and use!
-->

## Getting involved

* [ Join ](https://groups.google.com/a/mlcommons.org/g/croissant) the mailing list
* Attend Croissant meetings (please joint the list to automatically receive the invite)
* [ File issues for ](https://github.com/mlcommons/croissant) bugs for feature requests
* [ Contribute code ](https://github.com/mlcommons/croissant) (please sign the MLCommons Association CLA  first!)

## Integrations
Forthcoming

## Licensing
Croissant project code and examples are licensed under Apache 2.

## Governance
Croissant is being developed by the community as a Task Force of the [MLCommons Association](http://mlcommons.org) Datasets Working Group.
The Task Force is open to anyone (as is the parent [Datasets working group](https://mlcommons.org/en/groups/datasets/)). 
The Task Force is co-chaired by [Omar Benjelloun](mailto:benjello@google.com) and [Elena Simperl](mailto:elena.simperl@kcl.ac.uk).

## Contributors
Albert Villanova (Hugging Face), Andrew Zaldivar (Google), Baishan Guo (Meta), Carole Jean-Wu (Meta), Ce Zhang (ETH Zurich), Costanza Conforti (Google), D. Sculley (Kaggle), Dan Brickley (Schema.Org), Eduardo Arino de la Rubia (Meta), Edward Lockhart (Deepmind), Elena Simperl (King's College London), Geoff Thomas (Kaggle), Joaquin Vanschoren (TU/Eindhoven, OpenML), Jos van der Velde (TU/Eindhoven, OpenML), Julien Chaumond (Hugging Face), Kurt Bollacker (MLCommons), Lora Aroyo (Google), Meg Risdal (Kaggle), Natasha Noy (Google), Newsha Ardalani (Meta), Omar Benjelloun (Google), Peter Mattson (MLCommons), Pierre Marcenac (Google), Pierre Ruyssen (Google), Pieter Gijsbers (TU/Eindhoven, OpenML), Prabhant Singh (TU/Eindhoven, OpenML), Quentin Lhoest (Hugging Face), Taniya Das (TU/Eindhoven, OpenML)

Thank you for supporting Croissant! 🙂
