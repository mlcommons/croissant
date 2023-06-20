# `ml:split`

Describes a ML data split, similarly to <https://www.wikidata.org/wiki/Q3985153>, but not necessarily constrained to training, validation or testing splits.

The split values specified in the Croissant config format express the
initial intent of the data as expressed by the initial dataset authors.

While it is useful to specify the splits information for ML practitioners to reproduce the original experiments the dataset was originally assembled for, nothing prevents ML practitioners to use the data for other purposes.

Known split values:

- [`ml:training_split`](training_split.md)
- [`ml:validation_split`](validation_split.md)
- [`ml:testing_split`](testing_split.md)
