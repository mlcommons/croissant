r"""Example script to serialize a JSON to valid Croissant JSON-LD.

# noqa: E501
# pylint: disable=line-too-long
Usage:
python scripts/serialize_from_json.py \
    --json "{\"@type\": \"sc:Dataset\", \"name\": \"PASS\", \"description\": \"PASS is a large-scale image dataset that does not include any humans and which can be used for high-quality pretraining while significantly reducing privacy concerns.\", \"@language\": \"en\", \"license\": \"https://creativecommons.org/licenses/by/4.0/\", \"url\": \"https://www.robots.ox.ac.uk/~vgg/data/pass/\"}"
# pylint: enable=line-too-long
# qa: E501
"""

import json

from absl import app
from absl import flags
from absl import logging

import ml_croissant as mlc

flags.DEFINE_string(
    "json",
    None,
    "JSON representation to convert to valid Croissant JSON-LD.",
)

FLAGS = flags.FLAGS


def main(argv):
    """Main function launched by the script."""
    del argv
    json_ = FLAGS.json
    json_ = json.loads(json_)
    metadata = mlc.nodes.Metadata.from_json(json_)
    # Check if there are errors:
    if metadata.issues.errors:
        logging.error(metadata.issues.report())
    # Serialize to JSON-LD:
    json_ = metadata.to_json()
    print(json.dumps(json_, indent=2))


if __name__ == "__main__":
    app.run(main)
