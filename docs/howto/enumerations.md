# How to specify enumerations

Enumerations are **finite** sets of values, which can be **named** or have an associated semantic meaning, but don't have to.

For example, the titanic dataset uses an enumeration to specify
the passengers gender, which can take two values: `male` and `female`.

Enumerations can be of various `dataType`s, but will most of the time be of type
[`sc:Text`](http://schema.org/Text).

While enumerations are often used to define [classes](/definitions/classes) or [labels](/definitions/labels),
they don't need to.

## Clarifications: enumerations, classes and labels

Because labels ([definition](definitions/label)) often refer to discrete values (e.g.
`{"cat", "dog"}`), and because the general definition of a label outside of ML and CS is "a kind of
tag to idendify an object", labels are often assimilated to classes.
However in ML, a label can also refer to a continuous value (e.g.
`temperature (float)`).

Classes ([definition](definitions/class)), while being defined
using enumerations, are often used in the context of classification
problems.

To avoid ambiguities and confusion, the Croissant
format does not use the terms "label" and "class" in the context of enumerations.

## Data type, name and semantic meaning

## Declaring enumerations

There are two ways to declare enumerations

### `ml:Field` enumeration

In the following example, extracted from the [coco2014 Croissant definition](https://github.com/mlcommons/croissant/blob/main/datasets/coco2014/metadata.json), the field `supercategory` is declared to be
an enumeration using the `"ml:isEnumeration": true` property.

https://github.com/mlcommons/croissant/blob/6c8eca2925191577a7101dcabd0a880aca03cae3/datasets/coco2014/metadata.json#L259-L271

The field is of `dataType` `sc:Text`

### `ml:RecordSet` enumeration

TODO: enumerations with keys vs no keys, with name vs no name.
JSON included declaration.

