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


def main(argv):
    del argv
    file = FLAGS.file
    dataset = datasets.Dataset(file)
    for record in dataset:
        print(f"Generating {record}")
        break
    print("Done.")


if __name__ == "__main__":
    app.run(main)
