"""Generates the dataset and yields the first example."""

from absl import app
from absl import flags

from format.src import datasets

flags.DEFINE_string(
    "file",
    None,
    "Path to the file to validate.",
)

flags.mark_flag_as_required("file")


FLAGS = flags.FLAGS

_NUM_MAX_RECORDS = 10


def main(argv):
    del argv
    file = FLAGS.file
    dataset = datasets.Dataset(file)
    print(f"Generating the first {_NUM_MAX_RECORDS} records.")
    for i, record in enumerate(dataset):
        if i >= _NUM_MAX_RECORDS:
            break
        print(record)
    print("Done.")


if __name__ == "__main__":
    app.run(main)
