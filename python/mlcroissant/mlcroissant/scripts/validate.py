"""Script to validate a Croissant JSON-LD file and output errors & warnings if any.

Usage:

```
mlcroissant validate --jsonld /path/to/file.json
```
"""

import sys

from absl import app
from absl import flags
from absl import logging

import mlcroissant as mlc

flags.DEFINE_string(
    "jsonld",
    None,
    "JSON-LD to validate (path to the file or URL).",
    required=True,
)

flags.DEFINE_string(
    "file",
    "",
    "[DEPRECATED] Path to the file to validate.",
    required=False,
)

flags.DEFINE_bool(
    "debug",
    False,
    "Whether to print debug hints.",
)

flags.mark_flag_as_required("jsonld")


FLAGS = flags.FLAGS


def main(argv):
    """Main function launched by the script."""
    del argv
    if FLAGS.file:
        logging.warning("--file is deprecated. Please, use --jsonld with a path or URL")
    jsonld = FLAGS.jsonld or FLAGS.file
    debug = FLAGS.debug
    try:
        mlc.Dataset(jsonld, debug=debug)
        logging.info("Done.")
    except mlc.ValidationError as exception:
        logging.error(exception)
        sys.exit(1)


if __name__ == "__main__":
    app.run(main)
