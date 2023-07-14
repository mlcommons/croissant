# `ml:label`

In ML, a **label** refers to the value being predicted i.e. the desired
output of a model.

While often referring to discrete values (e.g.`{"cat", "dog"}`), a label can also refer to a continuous value, for example a predicted temperature or price.

**Note**
Because labels often refer to discrete values, it may be used to designate an
[enumeration value](/howto/enumerations) or a class ([definition](/definitions/class)). Also, the general definition of a "label" outside of ML is
"a kind of tag to idendify an object". To avoid ambiguities and confusion,
the Croissant format only uses `ml:label when it matches the above
definition. See the [howto define labels documentation](/howto/labels) to
use all kind of labels.
