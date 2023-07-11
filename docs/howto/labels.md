# How to specify classes

**Note**



Often, datasets contain labels: human readable descriptions (usually a word or
a short text, such as "cat", "dog", etc.) informing what a particular piece of
data is about. A label can apply to an image, a sound, a video, a text or any
other type of data.

TODO: distinguish ML label, used for classification, from human-readable labels.

## Declaring a field as a label

Labels 

To mark a field as being a label, in addition of the `dataType` describing
the primordial type of the data, one must add the type `"sc:name"`.

For example, in the [coco2014 datasets](
https://github.com/mlcommons/croissant/blob/main/datasets/coco2014/metadata.json),
the `"categories"` `RecordSet`  have a label named `name`:

https://github.com/mlcommons/croissant/blob/0f8a1b408a6d225bf777a7dbddc47133d0eb0ea6/datasets/coco2014/metadata.json#L248-L257

Declaring a field as a label indicates that:

1. the field value (i.e. the label) can be used
to name the data it describes and that this name is suitable for human
usage, for example to display in a UI.
2. the field provides some kind of classification which can be used to train or evaluate a ML model.

## Labels scope

The label describes the parent entity, whether that's a record (if the label is
a "root-level" `Field`), or a `Field`, if the label is defined as a subfield.

Example of a label which describes a full record (here an image):

```json
{
    "name": "images",
    "description": "Images of cats and dogs (one animal per image).",
    "@type": "ml:RecordSet",
    "field": [
    {
        "name": "image",
        "description": "The image",
        ...
    },
    {
        "name": "label",
        "description": "One of {dog,cat}, animal on image.",
        "dataType": [
            "sc:Text",
            "sc:name"
        ],
        ...
    },
    ...
    ]
}
```

Example of a label which describes a field (here a bounding box):

```json
{
    "name": "images",
    "description": "Images of cats and dogs, possibly mixed.",
    "@type": "ml:RecordSet",
    "field": [
    {
        "name": "image",
        "description": "The image",
        ...
    },
    {
        "name": "annotations",
        "description": "Bounding boxes and their label.",
        "dataType": "ml:RecordSet",
        "subField": [
            {
              "name": "bbox",
              "@type": "ml:Field",
              "dataType": "ml:BoundingBox",
              ...
            },
            {
              "name": "label",
              "description": "One of {dog,cat}, animal in bbox.",
              "dataType": [
                  "sc:Text",
                  "sc:name"
              ],
              ...
            },
        ],
        ...
    },
    ...
    ]
}
```

## Labels and enumerations

Although they don't have to, labels are usually defined in conjunction with
[enumerations](), which differenciates them from captions: in any given dataset
with labels, one expects to see many rows using the same label, while most
captions would be unique.

Looking back at the [coco2014 datasets](
https://github.com/mlcommons/croissant/blob/main/datasets/coco2014/metadata.json)
example, one can see the the `"categories"` `RecordSet` has two labels: `name`
and `supercategory`:

```json
{
    "name": "categories",
    "@type": "ml:RecordSet",
    "ml:isEnumeration": true,
    "key": "#{id}",
    "field": [
    {
        "name": "id",
        "description": "The ID of the category",
        ...
    },
    {
        "name": "name",
        "description": "The name of the category.",
        "dataType": [
            "sc:Text",
            "sc:name"
        ],
        ...
    },
    {
        "name": "supercategory",
        "ml:isEnumeration": true,
        "description": "The name of the supercategory.",
        "dataType": [
            "sc:Text",
            "sc:name"
        ],
        ...
    }
    ]
},
```

In the above example, we know `supercategory` has a smaller cardinality than
`name`, because it's a field marked with `"ml:isEnumeration": true,` in a
`"ml:isEnumeration": true,` `RecordSet`.