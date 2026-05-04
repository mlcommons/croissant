"""Simple Croissant Tasks validator."""

import sys
from pyshacl import validate
from rdflib import Graph


def validate_data(
    data_path,
    shapes_path="croissant-tasks-shapes.ttl",
    ont_path="croissant-tasks.ttl",
):
  data_graph = Graph()
  data_graph.parse(data_path, format="json-ld")

  shapes_graph = Graph()
  shapes_graph.parse(shapes_path, format="turtle")

  ont_graph = Graph()
  ont_graph.parse(ont_path, format="turtle")

  conforms, results_graph, results_text = validate(
      data_graph,
      shacl_graph=shapes_graph,
      ont_graph=ont_graph,
      inference="rdfs",
      serialize_report_graph=True,
  )
  return conforms, results_text


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Usage: python validator.py <data.jsonld>")
    sys.exit(1)

  conforms, results_text = validate_data(sys.argv[1])
  if conforms:
    print("✅ Valid! Inheritance recognized.")
  else:
    print("❌ Invalid data.")
    print(results_text)
