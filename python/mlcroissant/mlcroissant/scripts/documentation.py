"""Generates the dataset and yields the first example."""

import datetime
from typing import TypedDict

from absl import app
from absl import flags
from absl import logging
from etils import epath
from rdflib import term

import mlcroissant as mlc
from mlcroissant._src.core import dataclasses as mlc_dataclasses

flags.DEFINE_string(
    "output",
    None,
    "The output folder.",
    required=True,
)

flags.mark_flag_as_required("output")


FLAGS = flags.FLAGS


class Url(TypedDict):
    """TypedDict with `url` and `name`."""

    url: str
    name: str


def main(argv):
    """Main function launched by the script."""
    del argv
    output = epath.Path(FLAGS.output)
    return documentation(output=output)


def documentation(output: epath.Path):
    """Creates the documentation."""
    if output.exists():
        logging.info(f"Path {output} already exists")
        output = output / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    output.mkdir(parents=True)
    import jinja2

    loader = jinja2.FileSystemLoader(epath.Path(__file__).parent / "templates")
    env = jinja2.Environment(loader=loader, autoescape=jinja2.select_autoescape())
    ctx = mlc.Context()
    for cls in [mlc.Field, mlc.FileObject, mlc.FileSet, mlc.Metadata, mlc.RecordSet]:
        fields = []
        for field in mlc_dataclasses.jsonld_fields(cls):
            url = field.call_url(ctx)
            url = Url(url=url, name=ctx.rdf.shorten_value(url))
            input_types = []
            for input_type in field.input_types:
                if isinstance(input_type, term.URIRef):
                    input_types.append(
                        Url(url=str(input_type), name=ctx.rdf.shorten_value(input_type))
                    )
                elif issubclass(input_type, mlc.Node):
                    jsonld_type = input_type._jsonld_type(ctx)
                    if isinstance(jsonld_type, term.URIRef):
                        input_types.append(
                            Url(
                                url=str(jsonld_type),
                                name=ctx.rdf.shorten_value(jsonld_type),
                            )
                        )
                    else:
                        input_types.append(Url(url="", name=input_type.__name__))
                else:
                    input_types.append(Url(url=str(input_type), name=""))
            details = {
                "cardinality": field.cardinality,
                "description": field.description,
                "input_types": input_types,
                "url": url,
            }
            fields.append(details)
        data = {
            "title": cls.__name__,
            "documentation": cls.__doc__,
            "fields": fields,
        }
        template = env.get_template("node.html")
        file = output / f"{cls.__name__}.html"
        file.write_text(template.render(data))
    print(f"Wrote documentation to {output}")


if __name__ == "__main__":
    app.run(main)
