import os
import sys
import unittest
from tasks.validator import validate_data


class TestCroissantTasksValidator(unittest.TestCase):

  def test_valid_problem(self):
    conforms, _ = validate_data("testdata/valid_problem.jsonld")
    self.assertTrue(conforms, "Valid problem should pass validation.")

  def test_invalid_problem(self):
    conforms, text = validate_data("testdata/invalid_problem.jsonld")
    self.assertFalse(conforms, "Problem with no specs should fail.")
    self.assertIn(
        "A TaskProblem must have at least one property (input, output, or"
        " implementation) that is a spec class",
        text,
    )

  def test_valid_solution(self):
    conforms, _ = validate_data("testdata/valid_solution.jsonld")
    self.assertTrue(conforms, "Valid solution should pass validation.")

  def test_invalid_solution(self):
    conforms, text = validate_data("testdata/invalid_solution.jsonld")
    self.assertFalse(conforms, "Solution without schema:isBasedOn should fail.")
    self.assertIn(
        "A TaskSolution must be formally linked to a TaskProblem via"
        " schema:isBasedOn",
        text,
    )

  def test_direct_task(self):
    conforms, _ = validate_data("testdata/direct_task.jsonld")
    self.assertTrue(conforms, "Direct Task with concrete values should pass.")

  def test_invalid_solution_with_spec(self):
    conforms, text = validate_data("testdata/invalid_solution_with_spec.jsonld")
    self.assertFalse(conforms, "Solution with spec should fail.")
    self.assertIn(
        "A TaskSolution cannot have an OutputSpec as output.",
        text,
    )

  def test_valid_solution_subtasks(self):
    conforms, _ = validate_data(
        "testdata/valid_solution_subtasks_all_concrete.jsonld"
    )
    self.assertTrue(
        conforms, "Solution with all concrete subtasks should pass."
    )

  def test_invalid_solution_subtasks(self):
    conforms, text = validate_data(
        "testdata/invalid_solution_subtasks_no_concrete_implementation.jsonld"
    )
    self.assertFalse(conforms, "Solution with spec subtask should fail.")
    self.assertIn(
        "All subTasks of a TaskSolution must have a concrete implementation.",
        text,
    )

  def test_valid_problem_with_execution_spec(self):
    conforms, _ = validate_data(
        "testdata/valid_problem_with_execution_spec.jsonld"
    )
    self.assertTrue(conforms, "Problem with ExecutionSpec should pass.")

  def test_invalid_problem_with_concrete_execution(self):
    conforms, text = validate_data(
        "testdata/invalid_problem_with_concrete_execution.jsonld"
    )
    self.assertFalse(conforms, "Problem with concrete execution should fail.")
    self.assertIn(
        "Execution property of a TaskProblem must be an ExecutionSpec.",
        text,
    )
  def test_valid_problem_with_evaluation_spec(self):
    conforms, _ = validate_data(
        "testdata/valid_problem_with_evaluation_spec.jsonld"
    )
    self.assertTrue(conforms, "Problem with EvaluationSpec should pass.")

  def test_invalid_solution_with_evaluation_spec(self):
    conforms, text = validate_data(
        "testdata/invalid_solution_with_evaluation_spec.jsonld"
    )
    self.assertFalse(conforms, "Solution with EvaluationSpec should fail.")
    self.assertIn(
        "A TaskSolution cannot have an EvaluationSpec as evaluation.",
        text,
    )

  def test_valid_evaluation_task(self):
    conforms, _ = validate_data("testdata/valid_evaluation_task.jsonld")
    self.assertTrue(conforms, "Valid evaluation task should pass validation.")


if __name__ == "__main__":
  unittest.main()

