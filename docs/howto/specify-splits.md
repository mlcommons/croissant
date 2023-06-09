# Howto specify ML data splits

ML datasets may come in [different data splits, intended to be used for different steps of a model building](https://en.wikipedia.org/wiki/Training,_validation,_and_test_data_sets), usually training, validation and testing.

The Croissant format allows for the data to be split arbitrarily into one or multiple splits, which for example allows dataset consumers to load a specific split.

## The split field

The splits definition is done at the `RecordSet` level, with a dedicated field which can be named "split" or anything else, but must have the semantic data type [`wd:Q3985153`](https://www.wikidata.org/wiki/Q3985153). That field data type is generally `sc:Text`, but could theoritically come as other data types, `sc:Integer` for example.

The following artificial example defines the split(s) based on a CSV column:

https://github.com/mlcommons/datasets_format/blob/3683ea494b8952c842496d523f4e2ed9ab785627/datasets/recipes/simple-split.json#L45-L54

Often, data from different splits come packaged into different files, which enable dataset consumers to only download the needed data. In such cases, the split definition is still done at the `RecordSet` level, but can refer to data file names or path.

The following example is extracted from the [COCO2014 dataset Croissant config](https://github.com/mlcommons/datasets_format/blob/main/datasets/coco2014/metadata.json):

<https://github.com/mlcommons/datasets_format/blob/2e05069f02a93e6154137aa267e69bd1271a95b0/datasets/coco2014/metadata.json#L173-L187>

As one would expect, tools working with the Croissant config format can still infer the packaged data files needed for each split, and if a user requests loading only the "test" split, then tools can avoid downloading the "train" split files.

While splits can already be used as it, a dataset publisher can add semantic information about the split names themselves, so they are easier to use in a standardized way, or can be used automatically by tools. This is the purpose of the `references` field in the above example, and this is described in the next section.

## Associating a semantic meaning to split names

Different names might refer to the same conceptual split. For example, `validation`, `valid`, `val`, `dev` all refer to the same split concept, and might be used indifferently depending on the dataset. The Croissant config does not intend to force dataset publishers in using a single term, but provides a way to associate a semantic meaning (ie: URL) to the used split names.

The above example shows how a split information can be attached to a `RecordSet`. To associate semantic meaning to the split values, one needs to "refer" to another `RecordSet` describing those splits. In the above example, this reference is done with the `references` field:

https://github.com/mlcommons/datasets_format/blob/2e05069f02a93e6154137aa267e69bd1271a95b0/datasets/coco2014/metadata.json#LL186C11-L186C23

The `split_enums` `RecordSet` is declared as a `name` (on which join is done), and the semantic value: a `sc:URL` of type [`wd:Q3985153`](https://www.wikidata.org/wiki/Q3985153):

https://github.com/mlcommons/datasets_format/blob/2e05069f02a93e6154137aa267e69bd1271a95b0/datasets/coco2014/metadata.json#L128-L153

and the data describing those splits actually come from a [CSV file](https://github.com/mlcommons/datasets_format/blob/main/datasets/coco2014/data/splits.csv):

https://github.com/mlcommons/datasets_format/blob/83dd4919ea32319703a0fa23ed013719548b4c03/datasets/coco2014/data/splits.csv#L1

As you can see, here the split URLs are from the [known supported types](https://github.com/mlcommons/datasets_format/blob/main/docs/croissant-spec.md#known-supported-data-types) (under `wd:Q3985153`):
\
> **Warning**
> The follow pages are under construction and might not exist yet.
 - https://mlcommons.org/definitions/training_split
 - https://mlcommons.org/definitions/validation_split
 - https://mlcommons.org/definitions/test_split

## Wrapping it up

And voilà! With this information, a consumer of a dataset should be able to load a particular split, either using the original name of the split as specified by the dataset publisher, or by using a more standardized appellation. This additional semantic allows tools to "understand" if a split is actually intended for training, validation or testing.