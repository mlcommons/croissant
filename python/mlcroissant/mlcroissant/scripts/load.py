"""Generates the dataset and yields the first example."""

import json
from typing import Any, Mapping

from absl import app
from absl import flags
from absl import logging
from etils import epath

import mlcroissant as mlc
from mlcroissant._src.tests.records import record_to_python

_NUM_MAX_RECORDS = 10


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
    "update_output",
    False,
    "Whether to update the JSONL output test files.",
)

flags.DEFINE_string(
    "mapping",
    None,
    "Mapping filename->filepath as a Python dict[str, str] to handle manual downloads."
    " If `document.csv` is the FileObject and you downloaded it to"
    ' `~/Downloads/document.csv`, you can specify `--mapping \'{"document.csv":'
    ' "~/Downloads/document.csv"}\'`.',
)

flags.mark_flag_as_required("jsonld")


FLAGS = flags.FLAGS


def main(argv):
    """Main function launched by the script."""
    del argv
    if FLAGS.file:
        logging.warning("--file is deprecated. Please, use --jsonld with a path or URL")
    jsonld = FLAGS.jsonld or FLAGS.file
    record_set = FLAGS.record_set
    num_records = FLAGS.num_records
    debug = FLAGS.debug
    update_output = FLAGS.update_output
    mapping = FLAGS.mapping
    return load(
        jsonld=jsonld,
        record_set=record_set,
        num_records=num_records,
        debug=debug,
        update_output=update_output,
        mapping=mapping,
    )


def load(
    jsonld: str,
    record_set: str | None,
    num_records: int = _NUM_MAX_RECORDS,
    debug: bool = False,
    update_output: bool = False,
    mapping: str | None = None,
):
    """Yields data from the `record_set` in the input Croissant file."""
    if not mapping:
        file_mapping: Mapping[str, Any] = {}
    else:
        try:
            file_mapping = json.loads(mapping)
        except json.JSONDecodeError as e:
            raise ValueError("--mapping should be a valid dict[str, str]") from e
    dataset = mlc.Dataset(jsonld, debug=debug, mapping=file_mapping)
    if record_set is None:
        record_sets = ", ".join([f"`{rs.name}`" for rs in dataset.metadata.record_sets])
        raise ValueError(f"--record_set flag should have a value in {record_sets}")
    records = dataset.records(record_set)
    generate_all_records = num_records == -1
    if generate_all_records:
        print(f"Generating all records from {jsonld}.")
    else:
        print(f"Generating the first {num_records} records from {jsonld}.")
    output_records = []
    for i, record in enumerate(records):
        if not generate_all_records and i >= num_records:
            break
        print(record)
        output_records.append(record_to_python(record))
    print("Done.")
    if update_output and not jsonld.startswith("http"):
        output_folder = epath.Path(jsonld).parent / "output"
        if not output_folder.exists():
            output_folder.mkdir()
        output_file = output_folder / f"{record_set}.jsonl"
        with output_file.open("w") as f:
            for output_record in output_records:
                output_record = json.dumps(output_record)
                f.write(f"{output_record}\n")
        print(f"Wrote pickle to {output_file}.")


if __name__ == "__main__":
    app.run(main)
