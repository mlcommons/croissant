# Howto specify ML data splits

ML datasets may come in [different data splits, intended to be used for different steps of a model building](https://en.wikipedia.org/wiki/Training,_validation,_and_test_data_sets), usually training, validation and testing.

The Croissant format allows for the data to be split arbitrarily into one or multiple splits, which for example allows dataset consumers to load a specific split.

## The split field

The splits definition is done at the `RecordSet` level, with a dedicated field which can be named "split" or anything else, but must have the semantic data type [`wd:Q3985153`](https://www.wikidata.org/wiki/Q3985153). That field data type is generally `sc:Text`, but could theoritically come as other data types, `sc:Integer` for example.

<https://github.com/mlcommons/datasets_format/blob/2e05069f02a93e6154137aa267e69bd1271a95b0/datasets/coco2014/metadata.json#L173-L187>
