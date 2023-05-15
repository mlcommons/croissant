import sys

from absl import app
from absl import flags
from absl import logging
from format.src import datasets
from format.src import errors

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
    try:
        datasets.Dataset(file)
        logging.info("Done.")
    except errors.ValidationError as exception:
        logging.error(exception)
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
