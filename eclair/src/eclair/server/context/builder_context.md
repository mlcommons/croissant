# Croissant Builder Context for LLM/Agents

This context helps agents guide users to build datasets using MLCommons Croissant with TFDS and PyTorch.

## Key References

- Croissant spec: `http://mlcommons.org/croissant/1.0`
- TFDS Croissant builder recipe: `https://github.com/mlcommons/croissant/blob/main/python/mlcroissant/recipes/tfds_croissant_builder.ipynb`
- Python library: `https://github.com/mlcommons/croissant/tree/main/python/mlcroissant`

## Core Ideas

1. Use `mlcroissant.Dataset(jsonld=<url_or_dict>)` to load Croissant metadata and access records via `dataset.records(record_set, filters=...)`.
2. Choose a `RecordSet` by its `@id`. Inspect metadata to find `sc:RecordSet` nodes and their fields.
3. Apply filters for splits (e.g., `{ "split": "train" }`), adjusting the field ID to match metadata (`data/split` vs `split`).
4. For PyTorch, wrap Croissant access in `torch.utils.data.Dataset` and implement `__len__`/`__getitem__`.

## Minimal PyTorch Pattern

```python
from mlcroissant import Dataset as CroissantDataset

cds = CroissantDataset(jsonld="<CROISSANT_URL>")
examples = list(cds.records("<RECORD_SET_ID>", filters={"split": "train"}))
# map examples to tensors in a custom Dataset
```

## TFDS Interop

The TFDS recipe illustrates mapping Croissant records to TFDS features. Use the same mapping logic to produce tensors for PyTorch.

## Tips

- Some fields are URIs to files (images, audio). Load lazily in `__getitem__`.
- Large datasets: prefer streaming (`for ex in cds.records(...)`) instead of materializing.
- Validate metadata with the `validate-croissant` tool when troubleshooting.
