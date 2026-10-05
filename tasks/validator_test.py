import unittest
from tasks.validator import validate_data


class TestCroissantTasksValidator(unittest.TestCase):

  def test_valid_problem(self):
    conforms, _ = validate_data("testdata/valid_problem.jsonld")
    self.assertTrue(conforms, "Valid problem should pass validation.")

  def test_invalid_problem(self):
    conforms, text = validate_data("testdata/invalid_problem_no_spec.jsonld")
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
    conforms, text = validate_data("testdata/invalid_solution_no_is_based_on.jsonld")
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

  # ── EveryEvalEver (E3) Integration Examples ─────────────────────────────

  def test_e3_mmlu_pro_problem(self):
    conforms, text = validate_data(
        "examples/every_eval_ever/mmlu_pro_problem.jsonld"
    )
    self.assertTrue(conforms, f"E3 MMLU-Pro TaskProblem should pass: {text}")

  def test_e3_mmlu_pro_solution_kimi_k2(self):
    conforms, text = validate_data(
        "examples/every_eval_ever/mmlu_pro_solution_kimi_k2.jsonld"
    )
    self.assertTrue(conforms, f"E3 MMLU-Pro TaskSolution should pass: {text}")

  def test_e3_mmlu_pro_combined_task(self):
    conforms, text = validate_data(
        "examples/every_eval_ever/mmlu_pro_combined_task.jsonld"
    )
    self.assertTrue(conforms, f"E3 MMLU-Pro Combined Task should pass: {text}")

  def test_e3_intercode_ctf_agentic_task(self):
    conforms, text = validate_data(
        "examples/every_eval_ever/intercode_ctf_agentic_task.jsonld"
    )
    self.assertTrue(conforms, f"E3 InterCode CTF Agentic Task should pass: {text}")

  def test_e3_vectara_hallucination_task(self):
    conforms, text = validate_data(
        "examples/every_eval_ever/vectara_hallucination_task.jsonld"
    )
    self.assertTrue(conforms, f"E3 Vectara Hallucination Task should pass: {text}")

  def test_e3_simpleqa_llm_judge_task(self):
    conforms, text = validate_data(
        "examples/every_eval_ever/simpleqa_llm_judge_task.jsonld"
    )
    self.assertTrue(conforms, f"E3 SimpleQA LLM Judge Task should pass: {text}")


if __name__ == "__main__":
  unittest.main()
