"""Generates the dataset and yields the first example."""

import json

from absl import app
from absl import flags
from etils import epath

import mlcroissant as mlc
from mlcroissant._src.tests.records import record_to_python

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

flags.DEFINE_bool(
    "update_output",
    False,
    "Whether to update the JSONL output test files.",
)

flags.mark_flag_as_required("file")


FLAGS = flags.FLAGS


def main(argv):
    """Main function launched by the script."""
    del argv
    file = FLAGS.file
    record_set = FLAGS.record_set
    num_records = FLAGS.num_records
    debug = FLAGS.debug
    update_output = FLAGS.update_output
    return load(
        file=file,
        record_set=record_set,
        num_records=num_records,
        debug=debug,
        update_output=update_output,
    )


def load(
    file: str,
    record_set: str | None,
    num_records: int = _NUM_MAX_RECORDS,
    debug: bool = False,
    update_output: bool = False,
):
    """Yields data from the `record_set` in the input Croissant file."""
    dataset = mlc.Dataset(file, debug=debug)
    if record_set is None:
        record_sets = ", ".join([f"`{rs.name}`" for rs in dataset.metadata.record_sets])
        raise ValueError(f"--record_set flag should have a value in {record_sets}")
    records = dataset.records(record_set)
    generate_all_records = num_records == -1
    if generate_all_records:
        print(f"Generating all records from {file}.")
    else:
        print(f"Generating the first {num_records} records from {file}.")
    output_records = []
    for i, record in enumerate(records):
        if not generate_all_records and i >= num_records:
            break
        print(record)
        output_records.append(record_to_python(record))
    print("Done.")
    if update_output:
        output_folder = epath.Path(file).parent / "output"
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
