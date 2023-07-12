"""Generates the dataset and yields the first example."""

import pickle

from absl import app
from absl import flags
from etils import epath
from ml_croissant import Dataset

_NUM_MAX_RECORDS = 10


flags.DEFINE_string(
    "file",
    None,
    "Path to the file to validate.",
)

flags.DEFINE_string(
    "record_set",
    None,
    "The name of the record set to generate.",
)

flags.DEFINE_integer(
    "num_records",
    _NUM_MAX_RECORDS,
    "The number of records to generate. Use `-1` to generate the whole dataset.",
)

flags.DEFINE_bool(
    "debug",
    False,
    "Whether to print debug hints.",
)

flags.DEFINE_bool(
    "update_pkl",
    False,
    "Whether to update the pickle test files.",
)

flags.mark_flag_as_required("file")


FLAGS = flags.FLAGS


def main(argv):
    del argv
    file = FLAGS.file
    record_set = FLAGS.record_set
    num_records = FLAGS.num_records
    debug = FLAGS.debug
    update_pkl = FLAGS.update_pkl
    dataset = Dataset(file, debug=debug)
    records = dataset.records(record_set)
    print(f"Generating the first {num_records} records.")
    pickled_records = []
    for i, record in enumerate(records):
        if num_records != -1 and i >= num_records:
            break
        print(record)
        pickled_records.append(record)
    print("Done.")
    if update_pkl:
        pickle_file = epath.Path(file).parent / "output.pkl"
        with pickle_file.open("wb") as f:
            pickle.dump(pickled_records, f)
        print(f"Wrote pickle to {pickle_file}.")


if __name__ == "__main__":
    app.run(main)
