# Croissant Dataset Format

- Version: 0.1
- Status: Early draft
- Edited collaboratively by members of the ML Datasets format working group.

This is the draft specification of `Croissant`, a format for ML
datasets. `Croissant` is based on [schema.org](https://schema.org), and builds on
its [Dataset](https://schema.org/dataset) vocabulary. The `Croissant` format is
defined under a separate namespace, although some parts of if may make sense to
integrate into `schema.org` down the line.

The main components of the `Croissant` format are:

- **Resource description**: The contents of a dataset as individual files
  (`FileObject`) and/or sets of files (`FileSet`).
- **Content structure**: The organization of the information inside the
  datasets as structured records (`RecordSet`) and their fields (`Field`).
- **ML semantics**: ML-specific information about the dataset: splits, labels,
  snapshots, etc.

We use the `sc` prefix to refer to the `http://schema.org` namespace.

## Classes

The `Croissant` vocabulary defines the following classes:

### FileObject

A digital file that could represent a
[sc:DigitalDocument](https://schema.org/DigitalDocument),
[sc:MediaObject](https://schema.org/MediaObject) or some other type of file.

`FileObject` is a general purpose class that should ideally be included in the
`schema.org` vocabulary.

**subclassOf**: [sc:CreativeWork](https://schema.org/CreativeWork)

**Properties**:

* [fileExtension](#fileextension): The extension of a file denoting its
  type, e.g., `.exe`, `.mp3`, `.pdf`.
* [containedIn](#containedin): A location that this object is
  contained in, e.g., in case it's extracted from an archive.

Notable inherited properties:

* [sc:name](https://schema.org/name) : Name is used as an identifier and should not
  contain special characters.
* [sc:contentUrl](https://schema.org/contentUrl): Actual bytes of the media object, for
  example the image file or video file.
* [sc:contentSize](https://schema.org/contentSize): File size in (mega/kilo)bytes.
* [sc:sameAs](https://schema.org/sameAs): The name or URL of a `FileObject` with
  the same content, but a different format.


### FileSet

A set of files located in a container, e.g. an archive, folder or manifest file,
potentially filtered by inclusion and/or exclusion filters.

`FileSet` is a general purpose class that should ideally be included in the
`schema.org` vocabulary.

**subclassOf**:	[sc:CreativeWork](https://schema.org/CreativeWork)

**Properties**:

*   [containedIn](#containedin): The container of the files in the `FileSet`.
*   [includes](#includes): A glob pattern that specifies the files to include,
    e.g., `"*.jpg" `.
*   [excludes](#excudes): A glob pattern that specifies the files to exclude.


### RecordSet

A `RecordSet` describes a set of structured records obtained from one or more data
sources (typically a file or set of files) and the structure of these records,
expressed as a set of fields (e.g., the columns of a table). A `RecordSet` can
represent flat or nested data.

A `RecordSet` can also be used to combine/flatten data from multiple sources,
typically to prepare data for ingestion by ML applications.

**subclassOf**:	[sc:Intangible](https://schema.org/Intangible)

**Properties**:

*   [source](#source): A data source for the records, typically a reference to a
    `FileObject` or `FileSet` of the form `"#{<source_name>}"`. A source can be
    a single structured file (e.g., a `csv` or `jsonl` `FileObject`) that yields
    one record per line, or a set of unstructured files (e.g., a directory of
    images) that yield one record per file.
*   [field](#field): A data element that appears in the records in the
    `RecordSet` (e.g., one column of a table).
*   [key](#key): One or more fields whose value uniquely identify each record in
    the `RecordSet`.
*   [record](#record): One or more inlined records that belongs to the `RecordSet`,
    typically used for small enumerations that do not have an external source of
    data.


### Field

A `Field` is a component of the structure of a `RecordSet`. It may represent a
column of a table, or a nested data structure or even a nested `RecordSet` in
the case of hierarchical data.

**subclassOf**:	[sc:Intangible](https://schema.org/Intangible)

**Properties**:

*   [source](#source): The data source of the field, or the form
    `"#{<record_source>/<field_source>}"`. For example if the source of records is a table,
    the field source is of the form `"#{<table_name>/<column_name>}"`.
*   [dataType](#datatype): The data type of the field, which could be either an
    atomic type (e.g, `sc:Integer`) or a semantic type (e.g., `sc:GeoLocation`).
*   [references](#references): Another `Field` of another `RecordSet` that this
    field references. This is the equivalent of a foreign key reference in a
    relational database.
*   [subField](#subfield): Another `Field` that is nested inside this one.
*   [parentField](#parentfield): A special case of `SubField` that should be
    hidden because it references a `Field` that already appears in the
    RecordSet.


### DataSource

A reference to a source of data. This class is generally used when the data
needs to be transformed or formatted, otherwise a `Reference` can be used
instead.

**subclassOf**:	[sc:Intangible](https://schema.org/Intangible)

**Properties**:

*   [data](#data): The referenced data source.
*   [applyTransform](#applutransform): A transformation to apply to the source
    data, e.g., a regular expression or json query.
*   [format](#format): A format to apply to the source data, e.g., a date format
    or number format.

### Reference

A reference to another object defined within the dataset. References are string
of the form `"#{[ref]}"`, where `ref` is either the name of an object defined in
the dataset (e.g., a `FileObject`, or a `RecordSet`), or one of its components
(e.g., a `Field` in a `RecordSet`). For the latter case, `ref` uses '/' to
represent nesting (e.g., `"#{recordset2/field5}"`).

subclassOf:	[sc:Text](https://schema.org/Text)


### BoundingBox

A `BoundingBox` describes an imaginary rectangle that outlines an object or a group of objects in an image.

## Properties

We now describe the properties defined as part of the `Croissant` vocabulary.

### containedIn

A location that the object is contained in, e.g., an archive `FileObject`. When
`containedIn` is specified, then the `contentUrl` of the object is evaluated
starting from the object specified by `containedIn` (e.g., a path within an
archive). If multiple values are provided for `containedIn`, then their union is
taken (e.g., this can be used to to combine files from multiple archives).

**range**: [Reference](#reference) (to a [FileObject](#fileobject) or
[FileSet](#fileset))

**domain**: [FileObject](#fileobject), [FileSet](#fileset)

### includes

A glob pattern over content Urls or filenames that specifies files to include in
a `FileSet`. If multiple values are provided, then their union is taken, i.e.,
any file matched by any of the include patterns is included.

The range of the property is text, assuming a default globbing syntax. A more
structured type can be introduced if we want to support multiple globbing
mechanisms.

**range**:	[sc:Text](https://schema.org/Text)

**domain**:	[FileSet](#fileset)


### excludes

A glob pattern or regular expression over content Urls or filenames that
specifies files to exclude from the `FileSet`. If multiple values are provided,
then their union is taken, i.e., any file matched by any of the exclude patterns
is excluded.

**range**:	[sc:Text](https://schema.org/Text)

**domain**:	[FileSet](#fileset)


### source

The source of the data for a `RecordSet` or `Field`. In the case of a
`RecordSet`, this can be one or more `FileObject`, `FileSet` or `RecordSet`. In
the case of a `Field`, this can be an addressable subset of the contents of a
`FileObject` or `FileSet` (e.g., the name of a column in a CSV file, or a known
property of a `FileSet` such as `"filename"` or `"content"`).

**range**:	[Reference](#reference), [DataSource](#datasource)

**domain**:	[RecordSet](#recordset), [Field](#field)


### key

The key of a `RecordSet`, i.e., the subset of its fields that uniquely
identifies each record. Multiple values can be provided to represent a composite
key. A `RecordSet` can only define a single key.

**range**: [Reference](#reference) (to 1+ [Field](#field))

**domain**: [RecordSet](#recordset)


### field

A field of a `RecordSet`. A field may have simple atomic values, e.g., in the
case of a table, or more complex values, such as a record with multiple fields
(e.g., [sc:geoCoordinates](https://schema.org/geoCoordinates) is composed of a
`latitude` and a `longitude`), or a `RecordSet` containing multiple records.

**range**:	[Field](#field)

**domain**:	[RecordSet](#recordset)


### subField

In case of a complex Field of a RecordSet, `subField` is used to describe a
field nested inside the parent field.

**range**:	[Field](#field)

**domain**:	[Field](#field)


### parentField

`parentField` is a special kind of nested `subField`, which references a field
already present in the parent record, and therefore should be hidden.

**range**:	[Field](#field)

**domain**:	[Field](#field)


### dataType

The data type of values expected for a Field in a RecordSet. This class is
inspired by the `Datatype` class in [CSVW](https://csvw.org/). In addition to
simple atomic types, we also support semantic types, such as `schema.org` types,
or types defined in other vocabularies. In case of complex types, their
corresponding properties must be defined using `subField`.

A field may have more than a single assigned `dataType`, in which case at least
one must inform about the expected type of data (eg: `sc:Text`), while other
types inform about the semantic being used, possibly semantics with ML meaning.

**range**:	[sc:Text](https://schema.org/Text), [sc:URL](https://schema.org/URL)

**domain**:	[Field](#field)

[🔗](#known-supported-data-types) Known supported data types:

| `dataType`                                                      | Usage                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**`sc:Boolean`**](https://schema.org/Boolean)                  | Describes a boolean.                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| [**`sc:Date`**](https://schema.org/Date)                        | Describes a date.                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| [**`sc:Float`**](https://schema.org/Float)                      | Describes a float.                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| [**`sc:Integer`**](https://schema.org/Integer)                  | Describes an integer.                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| [**`sc:Text`**](https://schema.org/Text)                        | Describes a string.                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| [**`sc:URL`**](https://schema.org/ImageObject)                  | Describes a URL.                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| [**`sc:ImageObject`**](https://schema.org/ImageObject)          | Describes a field containing the content of an image (pixels).                                                                                                                                                                                                                                                                                                                                                                                                |
| [**`ml:BoundingBox`**](http://mlcommons.org/schema/BoundingBox) | Describes a bounding box.                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| [**`sc:name`**](https://schema.org/name)                        | Describes a field which can be used as a human-friendly label.                                                                                                                                                                                                                                                                                                                                                                                                |
| [**`ml:split`**](https://mlcommons.org/definitions/split)       | Describes a field used to divide data into multiple sets according to intended usage with regards to models [training](https://mlcommons.org/definitions/training_split), [validation](https://mlcommons.org/definitions/validation_split), [testing](https://mlcommons.org/definitions/test_split), and possibly others. <br/>While any value is acceptable here, it is recommended to associate the usual splits listed above with the linked semantic URL. |

Extension mechanism

The Croissant format supports more data types, which can be used by tools consuming the data. For example:

 | `dataType`                                                                | Usage                                                                                                                                                                                                                                                                                                                                                                   |
 | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
 | [**`wd:Q48277`**](https://www.wikidata.org/wiki/Q48277) <br/>(**gender**) | Describes a field which values are indicative of a person gender. This can be used by Ethical AI tools to flag possible gender bias in the data. Values for this field can be associated with specific gender URLs (eg: [**`wd:Q6581097`** (male)](https://www.wikidata.org/wiki/Q6581097), [**`wd:Q6581072`** (female)](https://www.wikidata.org/wiki/Q6581072), etc.) |


In the following example, `color_sample` is a field containing an image, but with no associated semantic meaning.

```json
{
  "name": "color_sample",
  "@type": "ml:Field",
  "dataType": "sc:ImageObject",
}
```

In the following example, the `url` field is expected to be a URL, which
semantic type is [City](https://www.wikidata.org/wiki/Q515), so one will expect
values of this field to be URLs referring to cities (eg:
“https://www.wikidata.org/wiki/Q90”).

```JSON
{
  "name": "url",
  "@type": "ml:Field",
  "dataType": [
    "https://schema.org/URL",
    "https://www.wikidata.org/wiki/Q515"
  ]
}
```


### references

A reference to another `field` of another `RecordSet`, with foreign key
semantics. If a `RecordSet` contains multiple references to fields of the same
target RecordSet, these are assumed to constitute a composite foreign key.

**range**: [Reference](#reference) (to a [Field](#field), or
[RecordSet](#recordset))

**domain**: [Field](#field)


### data

In a `DataSource` object, this property specifies the data source that is being
referenced (e.g., a `FileObject`, `RecordSet` or `Field`).

**range**: [Reference](#reference)

**domain**: [DataSource](#datasource)

### record

In a `RecordSet` object, this property defines the RecordSet data inline. This
inline mechanism is only expected to be used with small `RecordSet` instances,
for example the ones defining enumerated values. In such a case, data is a JSON
list, and each object within that list must define the RecordSet fields.


**Example**:

```JSON
{
  "@type": "ml:RecordSet",
   "name": "gender_enums",
   "description": "Maps gender keys (0, 1) to labeled values.",
   "key": "#{key}",
   "field": [
     { "name": "key", "@type": "ml:Field", "dataType": "sc:Integer" },
     { "name": "label", "@type": "ml:Field", "dataType": "sc:String" }
   ],
   "data": [
     { "key": 0, "label": "Male" },
     { "key": 1, "label": "Female" }
   ]
}
```

**range**: JSON Text that matches the fields of the `RecordSet`. TODO: Consider
switching to use `sc:PropertyValue` to keep the json-ld valid.

**domain**: [RecordSet](#recordset)

### applyTransform

A transformation to apply on source data. We aim to support a few simple
transformations:

- **delimiter**: split a string into an array using the supplied character
- **regex**: A regular expression to parse the data. TODO: Mechanism to specify if
             it applies to the entire file or to individual lines.
- **json-query**: A json query to evaluate on the (json) data source.

We can either define a custom type that has properties for each of these
mechanisms, or use `sc:PropertyValue` as an escape hatch.

**range**: [PropertyValue](https://schema.org/PropertyValue) TODO: Define a dedicated class.

**domain**: [DataSource](#datasource)

### format

A format used to parse the values coming from a `DataSource` e.g., for dates or numbers.

For bounding boxed, one of `CENTER_XYWH`, `XYWH`, `XYXY` or `REL_XYXY`, as defined by https://keras.io/api/keras_cv/bounding_box/formats/.

TODO: Define the list of supported formats, and devise a mechanism to select the
right format for a given target data type.

**range**: [sc:Text](https://schema.org/Text)

**domain**: [DataSource](#datasource)

## Open issues/questions

1. Representation of ML tasks
1. Do we need parentField?
1. Which namespace should Reference exist under?
1. Should Reference be this general, or should it be specialized into
   FileObjectReference, RecordSetReference, etc..?  (A bit verbose, but more
   type-safe, and helps with namespace homing.)
1. Representation of enumerated records: PropertyValue vs arbitrary JSON.
