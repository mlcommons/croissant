# How to specify enumerations

Enumerations are **finite** sets of values, which may be **named** and may
have an associated **semantic meaning**.

**Note**
While enumerations may be used to define [classes](/definitions/classes) or [labels](/definitions/labels), they don't mecessarily share the same meaning, check the definitions.

Although often being of `dataType` [`sc:Text`](http://schema.org/Text), enumerations can also be of other `dataType`s (e.g. `sc:Integer`).

For example, the titanic dataset uses an enumeration to specify
that the passengers gender field, of type `sc:Text`, can only take two values: `male` or `female`.

## Declaring enumerations

There are two ways to declare enumerations:

1. Directly on a `ml:Field`. This is a simple way to define an enumeration
   but has some limitations discussed below.
2. Using a dedicated `ml:RecordSet`, holding the enumeration values. Such
   definition allows enumerations to be fully defined, with a name and a
   semantic URL.

### `ml:Field` enumeration

In the following example, extracted from the [coco2014 Croissant definition](https://github.com/mlcommons/croissant/blob/main/datasets/coco2014/metadata.json), the field `supercategory` is declared to be
an enumeration using the `"ml:isEnumeration": true` property. This means that
there is a finite number of `supercategory` values, and that it is expected
that many rows will have the same value.

https://github.com/mlcommons/croissant/blob/6c8eca2925191577a7101dcabd0a880aca03cae3/datasets/coco2014/metadata.json#L259-L271

The field is of `dataType` `sc:Text`, but also has the type `sc:name`. This
means that `supercategory` is expected to be a text, and that this text is
the name of the enumeration value   ` naming itself (the
supercategory), makes sense to humans, and could therefore be used as it in
UIs.

Although being straightforward, this approach of defining an enumeration has several limitations:

1. The only way to know the cardinality of the enumeration (the number of
   distinct values it can take), is to read the full `RecordSet` in which
   the enumeration is defined, or to have data format native support for
   enumerations.
2. It doesn't allow specifying an enumeration value, a name and a semantic URL
   together. If the underlying format allows it (e.g. Parquet), one might
   declare an enumeration value (0, 1, 2, etc.) and a name, but no semantic
   URL.

For the above reasons, it is recommended to use a `RecordSet` to define an
enumeration unless:

1. the data format used by to store the `RecordSet` natively supports the
  concept of enumerations, which should make it fast to list all possible
  enumerations.\
  or
2. the `RecordSet` in which the enumeration is defined is known to be small.
  This is the case in the example above, as the parent `RecordSet` is being
  used to define another enumeration.

### `ml:RecordSet` enumeration

In the following example, also extracted from the [coco2014 Croissant definition](https://github.com/mlcommons/croissant/blob/main/datasets/coco2014/metadata.json), the `categories` `ml:RecordSet` is declared as being an enumeration:

https://github.com/mlcommons/croissant/blob/6c8eca2925191577a7101dcabd0a880aca03cae3/datasets/coco2014/metadata.json#L237-L271

That enumeration is then referenced from another `ml:RecordSet`, with a field
referencing the enumeration `categories` `ml:RecordSet`:

https://github.com/mlcommons/croissant/blob/6c8eca2925191577a7101dcabd0a880aca03cae3/datasets/coco2014/metadata.json#L284-L291

When declaring an enumeration using a `ml:RecordSet`, that `ml:RecordSet` is
expected to have at least one key field (here named `id`), which may be of
various `dataType`s, but will most often be of type `sc:Integer` or `sc:Text`.

As also described in the [labels howto](/howto/labels), the `ml:RecordSet` may
also have fields of the following type:

- `sc:name`, which may be the same field as the key field, if the key is of
type `sc:Text`. That field holds a human readable name of what the
enumeration value is about.
- `sc:URL`, which provide a semantic meaning to the enumeration value meaning.
That field may have an additional associated URL providing a general
semantic meaning to the enumeration.

The following example, extracted from the [titanic definition](https://github.com/mlcommons/croissant/blob/82a39dc23a062b8481f427bbc67110b93049f0c6/datasets/titanic/metadata.json), shows the usage
of the `sc:URL` field. It also shows how the key and name can be provided by
the same field.

https://github.com/mlcommons/croissant/blob/82a39dc23a062b8481f427bbc67110b93049f0c6/datasets/titanic/metadata.json#L55-L84

Not only the `dataType` of the `url` field in the above example is `sc:URL`,
it is also ['wd:Q48277' (gender)](https://www.wikidata.org/wiki/Q48277), to
indicate that the enumeration is being used to designate genders.

This enumeration `ml:RecordSet` contains only two records (`{"male", "female"`}), and each have the corresponding associated semantic URLs
([wd:Q6581097](https://www.wikidata.org/wiki/Q6581097): male,
[wd:Q6581072](https://www.wikidata.org/wiki/Q6581072): female):

https://github.com/mlcommons/croissant/blob/main/datasets/titanic/data/genders.csv
