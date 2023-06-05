WARNING: `metadata.json` is  incomplete and does not fully define the Oxford 102 category flower dataset. It lacks:

 - Image segmentations
 - &Chi2 distances
 - Human readable labels (flower names)

`metadata.json` provides an example on how splits can be defined at the `recordSet` level, in this case by matching the record ID to lists of IDs.

TODO: this dataset also defines image labels using an implicit index (starting from 1), which should probably be supported in Croissant.
