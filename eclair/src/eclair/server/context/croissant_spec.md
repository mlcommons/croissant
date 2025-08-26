# Croissant Format Specification

## Introduction

The Croissant metadata format simplifies how data is used by ML models. It provides a vocabulary for dataset attributes, streamlining how data is loaded across ML frameworks. In doing so, Croissant enables the interchange of datasets between ML frameworks and beyond.

### Portability and Reproducibility

Croissant provides sufficient information for an ML tool to load a dataset, allowing users to incorporate Croissant datasets in the training and evaluation of a model with just a few lines of code. Croissant can easily be added to any tools e.g., for data preprocessing, analysis and visualization, or labeling. Since the format is standardized, any Croissant-compliant tool will have an identical interpretation of the data. Furthermore, the information stored in a Croissant record attached to a dataset helps people understand its content and context and compare it with other datasets. All this leads to increased portability and reproducibility in the entire ML ecosystem.

Creating or changing the metadata is straightforward. A dataset repository can infer it from existing documentation such as a data card; beyond that, editing Croissant dataset descriptions is also supported through a visual editor and a Python library.

### Responsible AI

One of the main instruments to operationalise responsible AI (RAI) is dataset documentation.

Croissant is designed to be modular and extensible. One such extension is the Croissant RAI vocabulary, which addresses 7 specific use cases, starting with the data life cycle, data labeling, and participatory scenarios to AI safety and fairness evaluation, traceability, regulatory compliance and inclusion. More details are available in the [Croissant RAI specification](http://mlcommons.org/croissant/RAI/1.0).

## Terminology

**Dataset**: A collection of data points or items reflecting the results of such activities as measuring, reporting, collecting, analyzing, or observing.

**Croissant dataset**: A dataset that comes with a description in the Croissant format. Note that the Croissant description of a dataset does not generally contain the actual data of the dataset. The data itself is contained in separate files, referenced by the Croissant dataset description.

**Data record**: A granular part of a dataset, such as an image, text file, or a row in a table.

**Recordset**: A set of homogeneous data records, such as a collection of images, text files, or all the rows in a table.

## Format Example

To understand the various pieces of a Croissant dataset description, let's look at an example, based on the [PASS](https://www.robots.ox.ac.uk/~vgg/data/pass/) dataset.

Croissant metadata is encoded in JSON-LD.

```json
{
  "@context": {
    "@language": "en",
    "@vocab": "https://schema.org/"
  },
  "@type": "sc:Dataset",
  "name": "simple-pass",
  "conformsTo": "http://mlcommons.org/croissant/1.0",
  "description": "PASS is a large-scale image dataset that does not include any humans ...",
  "citeAs": "@Article{asano21pass, author = \"Yuki M. Asano and Christian Rupprecht and ...",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "url": "https://www.robots.ox.ac.uk/~vgg/data/pass/",
```

The beginning of the Croissant description contains general information about the dataset such as name, short description, license and URL. Most of these attributes are from [schema.org](http://schema.org), with a few additions described in the [Dataset-level information](#dataset-level-information) section.

```json
  "distribution": [
    {
      "@type": "cr:FileObject",
      "@id": "metadata.csv",
      "contentUrl": "https://zenodo.org/record/6615455/files/pass_metadata.csv",
      "encodingFormat": "text/csv",
      "sha256": "0b033707ea49365a5ffdd14615825511"
    },
    {
      "@type": "cr:FileObject",
      "@id": "pass9",
      "contentUrl": "https://zenodo.org/record/6615455/files/PASS.9.tar",
      "encodingFormat": "application/x-tar",
      "sha256": "f4f87af4327fd1a66dd7944b9f59cbcc"
    },
    {
      "@type": "cr:FileSet",
      "@id": "image-files",
      "containedIn": { "@id": "pass9" },
      "encodingFormat": "image/jpeg",
      "includes": "*.jpg"
    }
  ],
```

The distribution property contains a description of the resources contained in the dataset, i.e., :

- files, represented using the `FileObject` class. This dataset contains one CSV file and one archive file.
- Directory & archive contents, represented using the `FileSet` class. In this dataset, the archive contains a set of jpeg image files.

See the [Resources](#resources) section for a complete description.

```json
  "recordSet": [
    {
      "@type": "cr:RecordSet",
      "@id": "images",
      "key": { "@id": "hash" },
      "field": [
        {
          "@type": "cr:Field",
          "@id": "images/image_content",
          "description": "The image content.",
          "dataType": "sc:ImageObject",
          "source": {
            "fileSet": { "@id": "image-files" },
            "extract": {
              "fileProperty": "content"
            }
          }
        },
        {
          "@type": "cr:Field",
          "@id": "images/hash",
          "description": "The hash of the image, as computed from YFCC-100M.",
          "dataType": "sc:Text",
          "source": {
            "fileSet": { "@id": "image-files" },
            "extract": {
              "fileProperty": "filename"
            },
            "transform": {
              "regex": "([^\\/]*)\\.jpg"
            }
          }
          "references": { "@id": "metadata/hash" }
        },
        {
          "@type": "cr:Field",
          "@id": "images/date_taken",
          "description": "The date the photo was taken.",
          "dataType": "sc:Date",
          "source": { "@id": "metadata/datetaken" }
        }
      ]
    }
  ]
```

Furthermore, we can describe the structure and the data types in the data using a simple schema that supports flat and nested records called `RecordSet`. In this example, the dataset defines a single `RecordSet`, with one record per image in the dataset. Each record has 3 fields:

- the content of the image
- the hash of the image, extracted from its filename
- the date the image was taken, extracted from the metadata CSV file

The [RecordSets](#recordsets) section explains how to define recordsets and fields, as well as extract, transform and join their data.

## Prerequisites

### ID and Reference Mechanism

In Croissant datasets, various elements need to be connected to each other. We therefore need a mechanism to define **identifiers** for parts of a dataset, and to reference them in other places.

We use the standard JSON-LD mechanism for IDs and references, which relies on using the special `@id` property. References to objects are also specified using the `@id` property. They can be differenciated from ID definitions by the fact that no other properties are specified within the same object, e.g., `{"@id": "flores200_dataset.tar.gz"}` is a reference.

Here are some examples of IDs and references to them.

A set of JSON files included in a tar archive:

```json
{
  "@type": "cr:FileObject",
  "@id": "flores200_dataset.tar.gz",
  "name": "Flores 200 archive",
  "description": "Flores 200 is hosted on a webserver.",
  "contentSize": "25585843 B",
  "contentUrl": "https://tinyurl.com/flores200dataset",
  "encodingFormat": "application/x-gziptar",
  "sha256": "b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6"
},
{
  "@type": "cr:FileSet",
  "@id": "flores200_dev_files",
  "name": "Flores 200 dev files",
  "description": "dev files are inside the tar.",
  "containedIn": { "@id": "flores200_dataset.tar.gz" },
  "encodingFormat": "application/json",
  "includes": "flores200_dataset/dev/*.dev"
}
```

A "foreign key" reference on column "movie_id" from a "ratings" table to a "movies" table:

```json
{
  "@type": "cr:RecordSet",
  "@id": "ratings",
  "name": "IMDB ratings",
  "field": [
    {
      "@type": "cr:Field",
      "@id": "ratings/movie_id",
      "name": "Movie id",
      "dataType": "sc:Integer",
      "references": { "@id": "movies/movie_id" }
    }
  ]
}
```

In the above example, the `@id` of a `field` is prefixed by the `@id` of the corresponding `RecordSet`. This ensures the uniqueness, and makes it possible to disambiguate between `field`s of the same name in different `RecordSet`s. In this example, both the ratings and movies `RecordSet`s have a movie_id `field`.

## Dataset-level Information

Croissant builds on the [schema.org/Dataset](http://schema.org/Dataset) vocabulary, which is widely adopted by datasets on the web. 

## Resources

Croissant datasets contain data. Resources describe how that data is organized. Croissant defines two types of resources:

- `FileObject` for individual files that are part of a dataset.
- `FileSet` for homogeneous sets of files that are part of the dataset (e.g., a directory of images).

While [schema.org/Dataset](http://schema.org/Dataset) defines a `distribution` property, it's insufficient to adequately represent the contents of a dataset, as each distribution corresponds to a single downloadable form of the dataset. In practice, datasets often use `distribution` to represent separate files that are part of the dataset, but that is technically not a correct use of the property, and is still insufficient to describe datasets with a more complex layout, which is often the case of ML datasets.

In Croissant, the `distribution` property contains one or more `FileObject` or `FileSet` instead of schema.org's `DataDownload.`

### FileObject

`FileObject` is the Croissant class used to represent individual files that are part of a dataset.

Let's look at a few examples of `FileObject` definitions.

First, a single CSV file:

```json
{
  "@type": "cr:FileObject",
  "@id": "pass_metadata.csv",
  "contentUrl": "https://zenodo.org/record/6615455/files/pass_metadata.csv",
  "encodingFormat": "text/csv",
  "sha256": "0b033707ea49365a5ffdd14615825511"
}
```

Next: An archive and some files extracted from it (represented via the `containedIn` property):

```json
{
  "@type": "cr:FileObject",
  "@id": "ml-25m.zip",
  "contentUrl": "https://files.grouplens.org/datasets/movielens/ml-25m.zip",
  "encodingFormat": "application/zip",
  "sha256": "6b51fb2759a8657d3bfcbfc42b592ada"
},
{
  "@type": "cr:FileObject",
  "@id": "ratings-table",
  "contentUrl": "ratings.csv",
  "containedIn": { "@id": "ml-25m.zip" },
  "encodingFormat": "text/csv"
},
{
  "@type": "cr:FileObject",
  "@id": "movies-table",
  "contentUrl": "movies.csv",
  "containedIn": { "@id": "ml-25m.zip" },
  "encodingFormat": "text/csv"
}
```

### FileSet

In many datasets, data comes in the form of collections of homogeneous files, such as images, videos or text files, where each file needs to be treated as an individual item, e.g., as a training example. `FileSet` is a class that describes such collections of files.

A `FileSet` is a set of files located in a container, which can be an archive `FileObject` or a "manifest" file. A FileSet may also specify inclusion / exclusion filters: these are file patterns that give the user flexibility to define which files should be part of the `FileSet`. For example, include patterns may refer to all images under one or more directories, which exclude patterns may be used to exclude specific images.

Let's now see some examples of how `FileSet` is used:

A zip file containing images:

```json
{
  "@type": "cr:FileObject",
  "@id": "train2014.zip",
  "contentSize": "13510573713 B",
  "contentUrl": "http://images.cocodataset.org/zips/train2014.zip",
  "encodingFormat": "application/zip",
  "sha256": "sha256"
},
{
  "@type": "cr:FileSet",
  "@id": "image-files",
  "containedIn": { "@id": "train2014.zip" },
  "encodingFormat": "image/jpeg",
  "includes": "*.jpg"
}
```

A zip file containing multiple `FileSet`s and `FileObject`s:

```json
{
  "@type": "cr:FileObject",
  "@id": "flores200_dataset.tar.gz",
  "description": "Flores 200 is hosted on a webserver.",
  "contentSize": "25585843 B",
  "contentUrl": "https://tinyurl.com/flores200dataset",
  "encodingFormat": "application/x-gzip",
  "sha256": "c764ffdeee4894b3002337c5b1e70ecf6f514c00"
},
{
  "@type": "cr:FileSet",
  "@id": "files-dev",
  "description": "dev files are inside the tar.",
  "containedIn": { "@id": "flores200_dataset.tar.gz" },
  "encodingFormat": "application/json",
  "includes": "flores200_dataset/dev/*.dev"
},
{
  "@type": "cr:FileSet",
  "@id": "files-devtest",
  "description": "devtest files are inside the tar.",
  "containedIn": { "@id": "flores200_dataset.tar.gz" },
  "encodingFormat": "application/json",
  "includes": "flores200_dataset/devtest/*.devtest"
},
{
  "@type": "cr:FileObject",
  "@id": "metadata-dev",
  "description": "Contains labels for the records in each line in the dev files.",
  "contentUrl": "flores200_dataset/metadata_dev.tsv",
  "containedIn": { "@id": "flores200_dataset.tar.gz" },
  "encodingFormat": "text/tsv"
},
{
  "@type": "cr:FileObject",
  "@id": "metadata-devtest",
  "description": "Contains labels for the records in each line in the devtest files.",
  "contentUrl": "flores200_dataset/metadata_devtest.tsv",
  "containedIn": { "@id": "flores200_dataset.tar.gz" },
  "encodingFormat": "text/tsv"
}
```

## RecordSets

While `FileObject` and `FileSet` describe the resources contained in a dataset, they do not tell us anything about the way the content within the resources is organized. This is the role of `RecordSet`.

A key challenge is that ML data comes in many different formats, including unstructured formats such as text, audio and video, and structured ones such as CSV and JSON. All these formats, no matter their level of machine-readable structuredness, need to be loaded into a common representation for ML purposes, and sometimes combined despite their heterogeneity.

`RecordSet` provides a common structure description that can be used across different modalities, in terms of records that may contain multiple fields. Unstructured content, like text and images, is represented as single-field records. Tabular data yields one record per row in the table, with fields for each column. Tree-structured data can be described with nested and repeated fields.

Let's introduce the relevant classes first, before illustrating how they are used through examples.

### RecordSet

A `RecordSet` describes a set of structured records obtained from one or more data sources (typically a file or set of files) and the structure of these records, expressed as a set of fields (e.g., the columns of a table). A `RecordSet` can represent flat or nested data.

In addition to `Field`s, RecordSet also supports defining a `key` for the records, i.e., one or more fields whose values are unique across the records. In case the RecordSet represents a small enumeration of values, those can be embedded directly via the `data` property. Larger `RecordSet`s will reference `FileObject`s or `FileSet`s for their data, via their field definitions, as we will see below.

### Field

A `Field` is part of a `RecordSet`. It may represent a column of a table, or a nested data structure or even a nested `RecordSet` in the case of hierarchical data.

Each field has a `name`, which is its unique identifier within the `RecordSet`, and a `dataType`, which can be either an atomic data type or a semantic type (more on that below).

`source` is the property that is used to specify where the data for the field comes from. This may be a `FileObject` or `FileSet`, or a specific subset (e.g., a particular column in a table, or values extracted through a regular expression).

A `Field` may reference another `Field` in another `RecordSet`, similarly to foreign keys in relational databases, so that they can be joined together.

Let's see a simple example: The ratings `RecordSet` below defines the fields user_id, movie_id, rating and timestamp. The movie_id field is a reference to another `RecordSet`, movies.

```json
{
  "@type": "cr:RecordSet",
  "@id": "ratings",
  "key": [{ "@id": "ratings/user_id" }, { "@id": "ratings/movie_id" }],
  "field": [
    {
      "@type": "cr:Field",
      "@id": "ratings/user_id",
      "dataType": "sc:Integer",
      "source": {
        "fileObject": { "@id": "ratings-table" },
        "extract": {
          "column": "userId"
        }
      }
    },
    {
      "@type": "cr:Field",
      "@id": "ratings/movie_id",
      "dataType": "sc:Integer",
      "source": {
        "fileObject": { "@id": "ratings-table" },
        "extract": {
          "column": "movieId"
        }
      },
      "references": {
        "@idfield": "movies/movie_id"
      }
    },
    {
      "@type": "cr:Field",
      "@id": "ratings/rating",
      "description": "The score of the rating on a five-star scale.",
      "dataType": "sc:Float",
      "source": {
        "fileObject": { "@id": "ratings-table" },
        "extract": {
          "column": "rating"
        }
      }
    },
    {
      "@type": "cr:Field",
      "@id": "ratings/timestamp",
      "dataType": "sc:Integer",
      "source": {
        "fileObject": { "@id": "ratings-table" },
        "extract": {
          "column": "timestamp"
        }
      }
    }
  ]
}
```

The ratings `RecordSet` above corresponds to a CSV table, declared elsewhere as a ratings table `FileObject`. Each field specifies as a source the corresponding column of the CSV file.

### DataSource

`RecordSet`s specify where to get their data via the `dataSource` property of Field. `DataSource` is the class describing the data that can be extracted from files to populate a `RecordSet`. This class should be used when the data coming from the source needs to be transformed or formatted to be included in the ML dataset; otherwise a simple `Reference` can be used instead to point to the source.

#### Format

A format string used to parse the values coming from a `DataSource`. For example, a date may be represented as the string "2022/11/10", and interpreted into the correct date via the format "yyyy/MM/dd". Formats correspond to a target data type.

### Data Types

Specifying data types on the `Fields` of `RecordSets` is crucial for data validation, and downstream processing, e.g., to enable ML frameworks to automatically populate the right data structures when loading datasets.

Croissant supports two kinds of data types: simple, atomic data types such as integers and strings, and semantic data types, which convey more meaning and can be structured (more on that below).

Data types can be specified at two levels:

- On individual `Field`s, to specify a type that each value of that specific field will conform to. This is a standard notion of typing, similar to, say, assigning a type to a column in a database table.
- On an entire `RecordSet`, to specify a type that each record conforms to, as well as possibly mandatory fields.

#### DataType

The data type of values expected for a `Field` in a `RecordSet`. A field may have more than a single assigned `dataType`, in which case at least one must be an atomic data type (e.g.: `sc:Text`), while other types can provide more semantic information, possibly in the context of ML.

#### Typing RecordSets

As mentioned above, Croissant supports setting the `dataType` of an entire `RecordSet`. This means that the records it contains are instances of the corresponding data type. For example, if a `RecordSet` has the data type [sc:GeoCoordinates](http://schema.org/GeoCoordinates), then its records will be geopoints with a latitude and a longitude.

More generally, when a `RecordSet`is assigned a `dataType`, some or all of its fields must be mapped to properties associated with the data type. 

A cities `RecordSet` with fields explicitly mapped to latitude and longitude:

```json
{
  "@id": "cities",
  "@type": "cr:RecordSet",
  "dataType": "sc:GeoCoordinates",
  "field": [
    {
      "@id": "cities/lat",
      "@type": "cr:Field",
      "equivalentProperty": "sc:latitude"
    },
    {
      "@id": "cities/long",
      "@type": "cr:Field",
      "equivalentProperty": "sc:longitude"
    }
  ]
}
```

### Hierarchical RecordSets

Croissant `RecordSet`s provide two mechanisms to represent hierarchical data:

#### Nested Fields

`Field`s may be nested inside other fields, via the `subField` property, which makes it possible to group fields logically inside records: for example, a field of type `sc:GeoCoordinates` may have two `subField`s: latitude and longitude. Here is what it looks like:

```json
{
  "@type": "cr:Field",
  "@id": "gps_coordinates",
  "description": "GPS coordinates where the image was taken.",
  "dataType": "sc:GeoCoordinates",
  "subField": [
    {
      "@type": "cr:Field",
      "@id": "gps_coordinates/latitude",
      "dataType": "sc:Float",
      "source": {
        "fileObject": { "@id": "metadata" },
        "extract": { "column": "latitude" }
      }
    },
    {
      "@type": "cr:Field",
      "@id": "gps_coordinates/longitude",
      "dataType": "sc:Float",
      "source": {
        "fileObject": { "@id": "metadata" },
        "extract": { "column": "longitude" }
      }
    }
  ]
}
```

#### Nested Records

Croissant also supports nesting (multiple) records inside a single record. This functionality is often needed to represent the structure of hierarchical formats like the contents of JSON files. It's also useful to "denormalize" data so as to create joins across multiple tables in preparation for loading them into an ML framework.

Here is an example where a set of "ratings" records (one per user) are nested inside movie records:

```json
{
  "@type": "cr:RecordSet",
  "@id": "movies_with_ratings",
  "key": { "@id": "movies_with_ratings/movie_id" },
  "field": [
    {
      "@type": "cr:Field",
      "@id": "movies_with_ratings/movie_id",
      "source": { "@id": "movies/movie_id" }
    },
    {
      "@type": "cr:Field",
      "@id": "movies_with_ratings/movie_title",
      "source": { "@id": "movies/title" }
    },
    {
      "@type": "cr:Field",
      "@id": "movies_with_ratings/ratings",
      "dataType": "cr:RecordSet",
      "parentField": {
        "source": { "@id": "ratings/movie_id" },
        "references": { "@id": "movies_with_ratings/movie_id" }
      },
      "subField": [
        {
          "@type": "cr:Field",
          "@id": "movies_with_ratings/ratings/user_id",
          "source": { "@id": "ratings/user_id" }
        },
        {
          "@type": "cr:Field",
          "@id": "movies_with_ratings/ratings/rating",
          "source": { "@id": "ratings/rating" }
        },
        {
          "@type": "cr:Field",
          "@id": "movies_with_ratings/ratings/timestamp",
          "source": { "@id": "ratings/timestamp" }
        }
      ]
    }
  ]
}
```

## ML-specific Features

We now introduce a number of features that are useful in the context of ML data.

### Categorical Data

In machine learning applications, it's often useful to know that some of the data is categorical in nature, and has a finite set of values that can be used, say, for classification. Croissant represents that information by using the [sc:Enumeration](https://schema.org/Enumeration) class from [schema.org](https://schema.org), as a `dataType` on `RecordSet`s that hold categorical data

For example, the [COCO](https://cocodataset.org/#format-data) dataset defines categories and super-categories ([Croissant definition](https://github.com/mlcommons/croissant/blob/main/datasets/1.0/coco2014/metadata.json)), to which are associated other parts of the dataset. Using Croissant, one can describe the COCO super-categories the following way:

```json
{
  "@id": "supercategories",
  "@type": "cr:RecordSet",
  "dataType": "sc:Enumeration",
  "key": { "@id": "supercategories/name" },
  "field": [
    {
      "@id": "supercategories/name",
      "@type": "cr:Field",
      "dataType": "sc:Text"
    }
  ],
  "data": [
    { "supercategories/name": "animal" },
    { "supercategories/name": "person" }
  ]
}
```

### Splits

ML datasets may come in different data splits, intended to be used for different steps of a model building, usually training, validation and test.

The Croissant format allows for the data to be split arbitrarily into one or multiple splits, which for example allows dataset consumers to load a specific split. This is done by:

1. defining the `cr:Split` semantic `dataType`; and by
2. referring to those split definitions from the partitioned `RecordSet`(s).

For example, the following `RecordSet` defines the "train", "val" and "test" splits as defined by the COCO dataset authors.

```json
{
  "@id": "splits",
  "@type": "cr:RecordSet",
  "dataType": "cr:Split",
  "key": { "@id": "splits/name" },
  "field": [
    { "@id": "splits/name", "@type": "cr:Field", "dataType": "sc:Text" },
    { "@id": "splits/url", "@type": "cr:Field", "dataType": "cr:Split" }
  ],
  "data": [
    { "splits/name": "train", "splits/url": "cr:TrainingSplit" },
    { "splits/name": "val", "splits/url": "cr:ValidationSplit" },
    { "splits/name": "test", "splits/url": "cr:TestSplit" }
  ]
}
```

The example above illustrates the benefit of the `url` field, used to disambiguate the meaning of names possibly designing the same concept (e.g. "train" and "training").

Once a datasets splits have been defined, any `RecordSet` can refer to those using a regular field, as done in the following example, also extracted from the COCO dataset croissant definition:

```json
{
  "@id": "images",
  "@type": "cr:RecordSet",
  "field": [
    {
      "@id": "images/split",
      "@type": "cr:Field",
      "source": {
        "fileSet": { "@id": "image-files" },
        "extract": { "fileProperty": "fullpath" },
        "transform": {
          "regex": "^(train|val|test)2014.zip/.+2014/.*\\.jpg$"
        }
      },
      "references": { "@id": "splits/name" }
    }
  ]
}
```

Note that the field here is named "split", but doesn’t need to: the information of this being a ML split comes from the `dataType` of the `RecordSet` it refers to. As one would expect, tools working with the Croissant config format can infer the data files needed for each split. So if a user requests loading only the validation split of the COCO 2014 dataset, the tool working with Croissant knows to download the file "val2014.zip", but not "train2014.zip" and "test2014.zip".

### Label Data

Most ML workflows use label data. In Croissant, we identify label data using the class `cr:Label`. Labels will typically appear as fields in a `RecordSet`. The default semantics is that labels apply to the record they are defined in.

```json
{
  "@type": "cr:RecordSet",
  "@id": "images",
  "field": [
    {
      "@type": "cr:Field",
      "@id": "images/image"
    },
    {
      "@type": "cr:Field",
      "@id": "images/label",
      "dataType": ["sc:Text", "cr:Label"]
    }
  ]
}
```

### BoundingBox

Bounding boxes are common annotations in computer vision. They describe imaginary rectangles that outline objects or groups of objects in images or videos. Croissant supports adding a format specification using the Keras bounding box format, specified through the property `cr:format`.

```json
{
  "@type": "cr:Field",
  "@id": "images/annotations/bbox",
  "description": "The bounding box around annotated object[s].",
  "dataType": "cr:BoundingBox",
  "source": {
    "fileSet": { "@id": "instancesperson_keypoints_annotations" },
    "extract": { "column": "bbox" },
    "format": "CENTER_XYWH"
  }
}
```

### SegmentationMask

Segmentation masks are common annotations in computer vision. They describe pixel-perfect zones that outline objects or groups of objects in images or videos. Croissant defines `cr:SegmentationMask` with two manners to describe them:

Segmentation mask as a polygon:

```json
{
  "@type": "cr:Field",
  "@id": "images/annotation/mask",
  "description": "The segmentation mask around annotated object[s].",
  "dataType": ["cr:SegmentationMask", "sc:GeoShape"],
  "source": {
    "fileSet": { "@id": "instancesperson_keypoints_annotations" },
    "extract": { "regex": "w+s(.*)" },
    "format": "X Y"
  }
}
```

Segmentation mask as an image:

```json
{
  "@type": "cr:Field",
  "@id": "images/annotation/mask",
  "description": "The segmentation mask around annotated object[s].",
  "dataType": ["cr:SegmentationMask", "sc:ImageObject"],
  "source": {
    "fileSet": { "@id": "instancesperson_keypoints_annotations" },
    "extract": { "column": "image" }
  }
}
```

- `sc:GeoShape` describes segmentation masks as a sequence of coordinates (polygon).
- `sc:ImageObject` describes segmentation masks as image overlays (with pixel = 0 outside of the mask and pixel = 1 inside the mask).