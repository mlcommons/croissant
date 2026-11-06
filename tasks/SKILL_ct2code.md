---
name: ct2code
description: >-
  Guides an agent to go from Croissant Tasks TaskProblem files and a baseline description to actual code implementations of the benchmark and a particular baseline, and generating the corresponding TaskSolution file.
---

# Croissant Tasks to Code — Agent Runbook

## Objective

You are given a Croissant Tasks **`TaskProblem`** file (JSON-LD) describing a benchmark and a description of a **baseline** (model, hyperparameters, prompt templates) that you want to test on it. Your job is to generate the code implementing that solution and the corresponding Croissant Tasks **`TaskSolution`** file.

The generated code should perform the following tasks:
1.  **Data loading**: Download and read the input dataset specified in the problem file.
2.  **Sub-task structure**: Implement necessary data processing and structure the code taking into account the `subTask` structure of the benchmark.
3.  **Implementation of baseline**: Implement the model API call (or local execution) for each sub-task, using the correct hyperparameters and prompts.
4.  **Evaluation**: Load or implement the evaluation metrics, compute them by comparing the output with golden labels, and log the metrics.
5.  **Croissant Task file writing**: Write the `TaskSolution` file, pointing to outputs and execution info, and correctly linking to the problem.

---

## Guidance

### Step 1: Analyze the `TaskProblem` File

Read the `TaskProblem` file to understand the benchmark structure:
- **Inputs**: Look for `croissant:input`. It might point to a Hugging Face dataset or a specific file.
- **Outputs**: Look for `croissant:output` and `OutputSpec` to understand the expected format of the predictions.
- **Subtasks**: Check if there are `croissant:subTask`s. If so, the implementation should likely handle them separately or iterate over them.
- **Evaluation**: Look for `croissant:evaluation` and `expectedMetric` to know what to measure.

### Step 2: Gather Baseline Information

You will need additional information not present in the `TaskProblem` file (which only defines the problem):
- **Model**: Which model to use (e.g., Gemini, GPT).
- **Hyperparameters**: Temperature, max tokens, etc.
- **Prompts**: Prompt templates for each sub-task if applicable.

This information can be provided as a **natural language description** in the user request or extracted from a referenced source (e.g., a paper's appendix). Alternatively, it can be provided as a **"skeleton" Croissant Tasks `TaskSolution` file** that contains the configuration but lacks the final results. The implementation should read this configuration and overwrite the file with the actual results after execution.

### Step 3: Generate Implementation Code

Generate Python code (or the language requested) that does the following:

#### 3.1 Data Loading
- Use appropriate libraries (e.g., `datasets` for Hugging Face) to load the data.
- Handle any authentication or downloading steps needed.

#### 3.2 Processing and Sub-tasks
- If the task has sub-tasks, structure the code to loop over them or call specific handlers.
- Align the data loading with the specific cuts/splits defined for each sub-task.

#### 3.3 Baseline Execution
- Implement the API call or model inference.
- Ensure hyperparameters are correctly passed.
- Apply prompt templates to the input data.

#### 3.4 Evaluation
- Extract golden labels from the loaded dataset.
- Compare model outputs with golden labels.
- **Implement all the metrics specified in the `TaskProblem`**. Do not use proxies or placeholders unless explicitly allowed by the user or strictly restricted by the environment.
- **Identify needed libraries**: If specific external libraries are required for proper metric calculation, the agent should check if they are available in the environment. If not, **ask the user to install them** instead of silently falling back to simplified proxies or placeholders.
- **Data Modality Checks**: Perform common-sense checks based on the data modality:
    - **Vision**:
        - **Coordinate Space**: Ensure prediction coordinates match ground truth scale (e.g., pixels vs normalized).
        - **Image Processing**: Verify color channel order (RGB vs BGR) and that resizing doesn't break coordinate mappings.
    - **Language**:
        - **Normalization**: Ensure consistent handling of casing, punctuation, and whitespace between predictions and references.
        - **Tokenization**: Be aware of different tokenization strategies that might affect metrics like BLEU or METEOR.
- **Robust Parsing**: Anticipate that LLMs may not follow strict output formats (like JSON) or might get truncated. Implement robust parsing with fallbacks or simpler plain text formats if needed.

#### 3.5 Output and Solution Generation
- Save the raw outputs (predictions) to a file.
- Save execution metadata (hyperparameters, timestamps) to a file.
- Generate the `TaskSolution` JSON-LD file.
- **Incremental Execution**: For long-running evaluations, consider implementing an incremental execution pattern by saving intermediate results to a file and skipping already processed samples on restart.

### Step 4: Generate `TaskSolution` File

The code should output a `TaskSolution` file that conforms to the Croissant Tasks spec.
- Set `@type` to `croissant:TaskSolution`.
- Link to the problem via `"schema:isBasedOn": { "@id": "<problem_id>" }`.
- Fill in `croissant:execution` with the actual hyperparameters used.
- **Correctly point to the location of the generated outputs and implementation files** (e.g., using relative paths within the repository or universally accessible URIs).
- Fill in `croissant:evaluation` with an `EvaluationTask` containing `EvaluationResult`s for each metric with their **latest concrete values**.
- **The `TaskSolution` MUST respect the `subTask` structure of the `TaskProblem`.** If the problem file defines `croissant:subTask`s, the solution file must also contain a `croissant:subTask` list, with each element being a `TaskSolution` pointing to the specific sub-task ID and containing its specific implementation, output, and evaluation results.

---

## Verification Plan for the Generated Code

The generated code should be verifiable. The agent should include instructions or tests to:
1.  **Dry Run**: Run on a small subset of data to verify the pipeline works.
2.  **Schema Check**: Verify that the generated `TaskSolution` file passes the Croissant Tasks validator.
3.  **Metric Verification**: Verify that the computed metrics match expected values if a small test case with known results is available.
4.  **Metric Plausibility Check**: If metrics are unexpectedly low (e.g., zero or near zero), double-check the implementation against the metric description in the paper or problem file. Common issues include coordinate format mismatches or parsing failures of LLM outputs.
