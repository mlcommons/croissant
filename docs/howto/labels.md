# How to specify labels

Often, datasets contain labels: human readable descriptions (usually a word or
a short text) that inform what a particular piece of data is about. A label
can apply to an image, a sound, a video, a text or any other type of data.

Although they don't have to, labels are usually defined in conjunction with
[enumerations]().

For example, in the [coco2014 datasets](
https://github.com/mlcommons/croissant/blob/main/datasets/coco2014/metadata.json),
`categories` have a label named `name`:

https://github.com/mlcommons/croissant/blob/0f8a1b408a6d225bf777a7dbddc47133d0eb0ea6/datasets/coco2014/metadata.json#L248-L257

The label applies to the containing object, wheather that's a record or a `Field`.
In the above example, the label is a `Field` from the `"categories"` `RecordSet`,
meaning the label applies to the full record.