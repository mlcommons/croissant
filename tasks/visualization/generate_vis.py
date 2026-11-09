#!/usr/bin/env python3
"""Script to generate Croissant Tasks visualization HTML."""

import argparse
import json
import os

def generate_visualization(problem_path, solution_path, template_path, output_path, align=False, hide_unsolved=False):
    """Generates the visualization HTML."""
    print(f"Reading problem from: {problem_path}")
    with open(problem_path, "r") as f:
        problem_data = json.load(f)

    print(f"Reading solution from: {solution_path}")
    with open(solution_path, "r") as f:
        solution_data = json.load(f)

    print(f"Reading template from: {template_path}")
    with open(template_path, "r") as f:
        template_content = f.read()

    # Replace placeholders
    filled_content = template_content.replace(
        "{{ PROBLEM_DATA }}", json.dumps(problem_data, indent=2)
    )
    filled_content = filled_content.replace(
        "{{ SOLUTION_DATA }}", json.dumps(solution_data, indent=2)
    )
    filled_content = filled_content.replace(
        "{{ ALIGN_SOLUTIONS }}", "true" if align else "false"
    )
    filled_content = filled_content.replace(
        "{{ HIDE_UNSOLVED }}", "true" if hide_unsolved else "false"
    )

    # In standalone file, we might want to embed visualizer.js content instead of linking it
    # if we want it to be truly standalone.
    # Let's see if we can read visualizer.js and embed it.
    visualizer_path = os.path.join(os.path.dirname(template_path), "visualizer.js")
    if os.path.exists(visualizer_path):
        print(f"Embedding visualizer.js from: {visualizer_path}")
        with open(visualizer_path, "r") as f:
            visualizer_js = f.read()
        filled_content = filled_content.replace(
            '<script src="visualizer.js"></script>',
            f"<script>\n{visualizer_js}\n</script>"
        )

    print(f"Writing visualization to: {output_path}")
    with open(output_path, "w") as f:
        f.write(filled_content)

def main():
    parser = argparse.ArgumentParser(description="Generate Croissant Tasks visualization.")
    parser.add_argument("--problem", required=True, help="Path to problem JSON-LD file.")
    parser.add_argument("--solution", required=True, help="Path to solution JSON-LD file.")
    parser.add_argument("--template", required=True, help="Path to template HTML file.")
    parser.add_argument("--output", required=True, help="Path to output HTML file.")
    parser.add_argument("--align", action="store_true", help="Align solutions with problems.")
    parser.add_argument("--hide_unsolved", action="store_true", help="Hide unsolved problems.")

    args = parser.parse_args()

    generate_visualization(args.problem, args.solution, args.template, args.output, args.align, args.hide_unsolved)

if __name__ == "__main__":
    main()
