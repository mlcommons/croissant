#!/usr/bin/env python3
"""Tests for generate_vis."""

import os
import unittest
from experimental.users.leobianco.croissant_tasks.visualization_js import generate_vis

class GenerateVisTest(unittest.TestCase):

    def test_generate_visualization(self):
        # Paths to real files for integration testing
        problem_path = "/google/src/cloud/leobianco/croissant-tasks/google3/experimental/users/leobianco/croissant_tasks/benchmark_examples/mmlu/mmlu_problem.jsonld"
        solution_path = "/google/src/cloud/leobianco/croissant-tasks/google3/experimental/users/leobianco/croissant_tasks/benchmark_examples/mmlu/mmlu_solution_small_fewshot.jsonld"
        template_path = "/google/src/cloud/leobianco/croissant-tasks/google3/experimental/users/leobianco/croissant_tasks/visualization_js/template.html"
        output_path = "/google/src/cloud/leobianco/croissant-tasks/google3/experimental/users/leobianco/croissant_tasks/benchmark_examples/mmlu/mmlu_visualization_test.html"

        # Ensure output file doesn't exist
        if os.path.exists(output_path):
            os.remove(output_path)

        generate_vis.generate_visualization(
            problem_path, solution_path, template_path, output_path
        )

        # Check if output file was created
        self.assertTrue(os.path.exists(output_path))

        # Clean up
        os.remove(output_path)

if __name__ == "__main__":
    unittest.main()
