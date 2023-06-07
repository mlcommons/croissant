"""validate script."""

import sys

from absl import app
from absl import flags
from absl import logging
from ml_croissant import Dataset, ValidationError

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
        Dataset(file)
        logging.info("Done.")
    except ValidationError as exception:
        logging.error(exception)
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
