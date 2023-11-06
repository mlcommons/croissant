import numpy as np

import mlcroissant as mlc

dataset = mlc.Dataset(file="../../datasets/flores-200/metadata.json", debug=False)
print(dataset)
# record_set = "language_translations_train_data_with_metadata"
record_set = "language_translations_train_data"
records = iter(dataset.records(record_set=record_set))
print(next(records))
print(next(records))
# for i, record in enumerate(records):
#     if type(record["language"]) is not bytes:
#         raise ValueError(f"failed on {record}, line {i}")
#     print(record)
