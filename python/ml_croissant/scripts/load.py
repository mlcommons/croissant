"""Generates the dataset and yields the first example."""

from absl import app
from absl import flags

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

flags.mark_flag_as_required("file")


FLAGS = flags.FLAGS


def main(argv):
    del argv
    file = FLAGS.file
    record_set = FLAGS.record_set
    num_records = FLAGS.num_records
    debug = FLAGS.debug
    dataset = Dataset(file, debug=debug)
    records = dataset.records(record_set)
    print(f"Generating the first {num_records} records.")
    for i, record in enumerate(records):
        if num_records != -1 and i >= num_records:
            break
        print(record)
    print("Done.")


if __name__ == "__main__":
    app.run(main)
