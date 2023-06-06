"""Generates the dataset and yields the first example."""

from absl import app
from absl import flags

from format.src import datasets

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

flags.mark_flag_as_required("file")


FLAGS = flags.FLAGS

_NUM_MAX_RECORDS = 10


def main(argv):
    del argv
    file = FLAGS.file
    record_set = FLAGS.record_set
    dataset = datasets.Dataset(file)
    records = dataset.records(record_set)
    print(f"Generating the first {_NUM_MAX_RECORDS} records.")
    for i, record in enumerate(records):
        if i >= _NUM_MAX_RECORDS:
            break
        print(record)
    print("Done.")


if __name__ == "__main__":
    app.run(main)
