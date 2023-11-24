# How to define labels

**Note**
The term label may designate several concepts. Please check the
[`ml:label` definition](/definitions/label).

This documentation page covers the following topics:

- Defining a [`ml:label`](/definitions/label), including a [class](/definitions/class).
- Defining a label following the general definition "a kind of tag to
  identify an object" or identifying tag.

## Defining a `ml:label`

To define a field as being a [`ml:label`](/definitions/label), one must just
add `ml:label` to its `dataType`s, for example:

```json
{
    "@type": "ml:RecordSet",
    "name": "weather_report",
    ...
    "field": [
        ...,
        {
            "@type": "ml:Field",
            "name": "air_temperature_c",
            "description": "The air temperature, taken in the shadow.",
            "dataType": ["sc:Number", "ml:label"],
            "source": "..."
        },
    ],
    ...
}
```

In the above example, the `air_temperature_c` field is declared as being a
`ml:label`, on top of being a number. This means that the dataset has
originally been collected to train models that could predict the air
temperature in ºC, given other parameters. Note that this does not prevent
anyone from using that same dataset for other purposes than predicting air
temperature: the `ml:label` `dataType` is indicative only.

### Defining a class

A class is the possible value a discrete `ml:label` may take. Discrete
values in Croissant are expressed using [enumerations](/howto/enumerations).

So to define a class, one can just define an enumeration and specify the type
`ml:label` on the field. For example:

```json
{
          "@type": "ml:Field",
          "name": "supercategory",
          "description": "The name of the supercategory.",
          "dataType": [
            "sc:Text",
            "sc:name",
            "sc:label"
          ],
          "isEnumeration": true,
}
```

In the above example, `supercategory` is a discrete text label, and the various
supercategories are all classes.

## Identifying tag

The term "label" can also refer to an identifying tag, or "a kind of tag to
idendify an object".

In croissant, there are two **complementary** ways to identify a record:

1. through a human-readable name, or/and
2. through a semantic URL.

The same mechanism is used to describe [enumerations](/howto/enumerations).

### Through a human-readable name

To mark a field as being a human-readable name, in addition of the
`dataType` describing the primordial type of the data, one must add the type
`sc:name`.

For example, in the [coco2014 datasets](
https://github.com/mlcommons/croissant/blob/main/datasets/coco2014/metadata.json),
the `"categories"` `RecordSet`  have a field named `name` with the type
`sc:name`:

https://github.com/mlcommons/croissant/blob/0f8a1b408a6d225bf777a7dbddc47133d0eb0ea6/datasets/coco2014/metadata.json#L248-L257

Declaring a field to be `sc:name` means that the field value can be used to
name the data it describes (see [scope](#scope-of-the-name-and-url) below)
and that this name is suitable for human usage, for example to display in a UI.

### Through a semantic URL

Similarly, one can declare a field to be of type `sc:URL`, meaning that the
field value is an URL at which there is a definition applicable to the data.

This mechanism is also used to define splits, for example in the
[coco2014 splits definition](https://github.com/mlcommons/croissant/blob/0f8a1b408a6d225bf777a7dbddc47133d0eb0ea6/datasets/coco2014/data/splits.csv):

https://github.com/mlcommons/croissant/blob/0f8a1b408a6d225bf777a7dbddc47133d0eb0ea6/datasets/coco2014/data/splits.csv

We also note that semantic URLs can also be used to define `dataType`s
themselves, [as described in the Croissant spec](
https://github.com/mlcommons/croissant/blob/0f8a1b408a6d225bf777a7dbddc47133d0eb0ea6/docs/croissant-spec.md#datatype).

### Scope of the name and url

A `sc:name` or a `sc:URL` describes the containing entity, whether that's a record
(the label is a "root-level" `Field`), or a `Field`, if the field is defined as
 a subfield.
