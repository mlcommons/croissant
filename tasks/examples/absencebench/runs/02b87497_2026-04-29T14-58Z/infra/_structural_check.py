"""Structural sanity check for AbsenceBench Croissant Tasks artifacts.

Workaround for the upstream SHACL validator (`tasks/validator.py`) which currently
fails on every input due to a malformed PropertyShape in
`croissant-tasks-shapes.ttl` (the property using `sh:or` of alternative paths
has no `sh:path` itself, which strict pyshacl rejects). See validator note in
README.md.

This script verifies:
  - JSON parses
  - JSON-LD parses into an RDF graph (rdflib)
  - Required types are present (TaskProblem / TaskSolution / OutputSpec / etc.)
  - Required structural references exist (schema:isBasedOn on solutions, etc.)
  - Subtask wiring is sensible

It does NOT replace SHACL — once the upstream shapes are fixed, switch back
to `tasks/validator.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import rdflib


CR = rdflib.Namespace("http://mlcommons.org/croissant/")
SCHEMA = rdflib.Namespace("https://schema.org/")


def _types(g: rdflib.Graph, node: rdflib.term.Node) -> set[rdflib.term.Node]:
  return set(g.objects(node, rdflib.RDF.type))


def check_problem(path: Path) -> tuple[bool, list[str]]:
  errs: list[str] = []
  with open(path) as f:
    raw = json.load(f)
  g = rdflib.Graph()
  g.parse(path, format="json-ld")

  problems = list(g.subjects(rdflib.RDF.type, CR.TaskProblem))
  if not problems:
    errs.append("No node typed croissant:TaskProblem")
    return False, errs

  root_iri = rdflib.URIRef(raw["@id"])
  if root_iri not in problems:
    errs.append(f"Root @id {root_iri} is not typed TaskProblem in the graph")

  for p in problems:
    out_specs = [
        o for o in g.objects(p, CR.output) if CR.OutputSpec in _types(g, o)
    ]
    in_specs = [
        o for o in g.objects(p, CR.input) if CR.InputSpec in _types(g, o)
    ]
    impl_specs = [
        o
        for o in g.objects(p, CR.implementation)
        if CR.ImplementationSpec in _types(g, o)
    ]
    has_some_spec = bool(out_specs or in_specs or impl_specs)
    refs_existing_spec = any(
        any(CR.OutputSpec in _types(g, o2) for o2 in g.objects(o, None))
        for o in g.objects(p, CR.output)
    )
    if not (has_some_spec or refs_existing_spec):
      errs.append(
          f"TaskProblem {p} has no Spec (OutputSpec/InputSpec/ImplementationSpec)"
          " and does not reference one."
      )

  for spec in g.subjects(rdflib.RDF.type, CR.OutputSpec):
    schemas = list(g.objects(spec, CR.schema))
    if not schemas:
      errs.append(f"OutputSpec {spec} has no croissant:schema")
      continue
    for s in schemas:
      if CR.RecordSet not in _types(g, s):
        continue
      fields = list(g.objects(s, CR.field))
      if not fields:
        errs.append(f"RecordSet {s} has no fields")
      for fld in fields:
        if not list(g.objects(fld, CR.dataType)):
          errs.append(f"Field {fld} has no dataType")

  ev_specs = list(g.subjects(rdflib.RDF.type, CR.EvaluationSpec))
  for ev in ev_specs:
    if not list(g.objects(ev, CR.expectedMetric)):
      errs.append(f"EvaluationSpec {ev} has no expectedMetric")

  return len(errs) == 0, errs


def check_solution(path: Path) -> tuple[bool, list[str]]:
  errs: list[str] = []
  with open(path) as f:
    raw = json.load(f)
  g = rdflib.Graph()
  g.parse(path, format="json-ld")

  solutions = list(g.subjects(rdflib.RDF.type, CR.TaskSolution))
  if not solutions:
    errs.append("No node typed croissant:TaskSolution")
    return False, errs

  root_iri = rdflib.URIRef(raw["@id"])

  for sol in solutions:
    if not list(g.objects(sol, SCHEMA.isBasedOn)):
      errs.append(f"TaskSolution {sol} missing schema:isBasedOn")
    for o in g.objects(sol, CR.output):
      if CR.OutputSpec in _types(g, o):
        errs.append(f"TaskSolution {sol} has OutputSpec as output (forbidden)")
    for o in g.objects(sol, CR.input):
      if CR.InputSpec in _types(g, o):
        errs.append(f"TaskSolution {sol} has InputSpec as input (forbidden)")
    for o in g.objects(sol, CR.implementation):
      if CR.ImplementationSpec in _types(g, o):
        errs.append(
            f"TaskSolution {sol} has ImplementationSpec as implementation"
            " (forbidden)"
        )
    for o in g.objects(sol, CR.evaluation):
      if CR.EvaluationSpec in _types(g, o):
        errs.append(
            f"TaskSolution {sol} has EvaluationSpec as evaluation (forbidden)"
        )

    own_impls = [
        o
        for o in g.objects(sol, CR.implementation)
        if CR.ImplementationSpec not in _types(g, o)
    ]
    subs = list(g.objects(sol, CR.subTask))
    if not own_impls and not subs:
      errs.append(
          f"TaskSolution {sol} has no concrete implementation and no subTasks"
      )
    if subs:
      for sub in subs:
        sub_impls = [
            o
            for o in g.objects(sub, CR.implementation)
            if CR.ImplementationSpec not in _types(g, o)
        ]
        if not sub_impls and root_iri == sol:
          errs.append(
              f"Sub-solution {sub} of root {sol} has no concrete implementation"
          )

  for ev in g.subjects(rdflib.RDF.type, CR.EvaluationTask):
    evaluated = list(g.objects(ev, CR.evaluatedSolution))
    if not evaluated:
      errs.append(f"EvaluationTask {ev} missing croissant:evaluatedSolution")
    results = list(g.objects(ev, CR.evaluationResults))
    for r in results:
      if not list(g.objects(r, CR.metric)):
        errs.append(f"EvaluationResult {r} missing croissant:metric")
      if not list(g.objects(r, CR.value)):
        errs.append(f"EvaluationResult {r} missing croissant:value")

  return len(errs) == 0, errs


def main() -> int:
  if len(sys.argv) < 2:
    print("Usage: python _structural_check.py <file.jsonld>")
    return 2
  path = Path(sys.argv[1])
  with open(path) as f:
    top = json.load(f)
  t = top.get("@type", "")
  if t == "croissant:TaskProblem":
    ok, errs = check_problem(path)
    label = "TaskProblem"
  elif t == "croissant:TaskSolution":
    ok, errs = check_solution(path)
    label = "TaskSolution"
  else:
    print(f"Unknown @type: {t!r}")
    return 2
  if ok:
    print(f"OK: {path} ({label}) is structurally valid")
    return 0
  print(f"FAIL: {path} ({label}) has {len(errs)} structural issue(s):")
  for e in errs:
    print(f"  - {e}")
  return 1


if __name__ == "__main__":
  raise SystemExit(main())
