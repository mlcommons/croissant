"""Script to validate a Croissant JSON-LD file and output errors & warnings if any.

Usage:

```
mlcroissant validate --file /path/to/file.json
```
"""

import sys

from absl import app
from absl import flags
from absl import logging

import mlcroissant as mlc

flags.DEFINE_string(
    "file",
    None,
    "Path to the file to validate.",
)

flags.DEFINE_bool(
    "debug",
    False,
    "Whether to print debug hints.",
)

flags.mark_flag_as_required("file")


FLAGS = flags.FLAGS


def main(argv):
    """Main function launched by the script."""
    del argv
    file = FLAGS.file
    debug = FLAGS.debug
    try:
        mlc.Dataset(file, debug=debug)
        logging.info("Done.")
    except mlc.ValidationError as exception:
        logging.error(exception)
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
