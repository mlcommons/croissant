# Croissant Tasks Report: SAGE-Eval

## Overview
- **Date**: 2026-05-02
- **Paper**: SAGE-Eval: Evaluating LLMs for Systematic Generalizations of Safety Facts (Chen Yueh-Han, Guy Davidson, Brenden M. Lake)
- **PDF**: /Users/ktgiahieu/Documents/croissant/tasks/automation/2505.21828v1.pdf
- **Paper URL**: https://arxiv.org/abs/2505.21828v1
- **Dataset URL**: https://huggingface.co/datasets/YuehHanChen/SAGE-Eval
- **@id base**: https://arxiv.org/abs/2505.21828v1

## Files emitted
| File | Type | Size |
|------|------|------|
| problem.jsonld | TaskProblem | 2154 bytes |
| solutions/*.jsonld | TaskSolution | ~1000 bytes x 15 |

## TaskProblem extraction

### High-confidence fields (explicitly stated)
| Field | Value | Paper section |
|-------|-------|---------------|
| name | SAGE-Eval | Abstract |
| description | Evaluates whether LLMs correctly apply well-established safety facts to naive user queries. | Abstract |
| input dataset | https://huggingface.co/datasets/YuehHanChen/SAGE-Eval | User prompt / Header |
| output schema | `model_response` (string) | Derived from task nature |
| metrics | Model-level Safety Score, Area under Safety Curve, Fact-level Safety Score | Section 3.2 |
| subtasks | Child, Animal, Chemical, Outdoor Activities, Medicine, Senior, Cybersecurity | Section 2.1 |

### Inferred fields (medium confidence)
| Field | Value | Rationale |
|-------|-------|-----------|
| None | N/A | Structure matches paper precisely. |

### Skipped (paper was silent)
| Field | Reason |
|-------|--------|
| Per-category metrics for baselines | The paper only reports aggregated model-level performance in Figure 2a and Table 10. |

## Solutions extracted

15 frontier models were extracted with their aggregated performance metrics:

| Model | Hyperparameters | Metrics → Values | Subtask breakdown |
|-------|-----------------|------------------|-------------------|
| claude-3-7-sonnet-20250219 | N/A | Model-level Safety Score=57.69, Area under Safety Curve=0.796 | None (Aggregated) |
| claude-3-5-sonnet-20241022 | N/A | Model-level Safety Score=49.04, Area under Safety Curve=0.727 | None (Aggregated) |
| gemini-1.5-pro | N/A | Model-level Safety Score=47.12, Area under Safety Curve=0.734 | None (Aggregated) |
| o1 | N/A | Model-level Safety Score=41.35, Area under Safety Curve=0.682 | None (Aggregated) |
| o3-mini | N/A | Model-level Safety Score=34.62, Area under Safety Curve=0.656 | None (Aggregated) |
| claude-3-5-haiku-20241022 | N/A | Model-level Safety Score=34.62, Area under Safety Curve=0.631 | None (Aggregated) |
| gemini-2.0-flash | N/A | Model-level Safety Score=30.77, Area under Safety Curve=0.685 | None (Aggregated) |
| DeepSeek-V3 | N/A | Model-level Safety Score=25.96, Area under Safety Curve=0.595 | None (Aggregated) |
| gpt-4o | N/A | Model-level Safety Score=24.76, Area under Safety Curve=0.548 | None (Aggregated) |
| Qwen2-72B-Instruct | N/A | Model-level Safety Score=17.31, Area under Safety Curve=0.496 | None (Aggregated) |
| Llama-3.3-70B-Instruct-Turbo | N/A | Model-level Safety Score=16.35, Area under Safety Curve=0.504 | None (Aggregated) |
| Meta-Llama-3.1-405B-Instruct-Turbo | N/A | Model-level Safety Score=16.35, Area under Safety Curve=0.519 | None (Aggregated) |
| o1-mini | N/A | Model-level Safety Score=14.42, Area under Safety Curve=0.490 | None (Aggregated) |
| gpt-4o-mini | N/A | Model-level Safety Score=11.54, Area under Safety Curve=0.400 | None (Aggregated) |
| Meta-Llama-3-70B-Instruct-Turbo | N/A | Model-level Safety Score=5.77, Area under Safety Curve=0.373 | None (Aggregated) |

## Validation results

| File | JSON | SHACL | Iterations | Remaining errors |
|------|------|-------|-----------|------------------|
| problem.jsonld | PASS | PASS | 2 | — |
| solutions/*.jsonld | PASS | PASS | 2 | — |

## Limitations / caveats
- Hyperparameters are not specified in the paper's main text for the baselines, so they are omitted.
- The subtask breakdown is defined abstractly in the `problem.jsonld` to reflect the 7 domains described in the paper, but subtask evaluations are not populated in the solutions since the specific per-domain results for each baseline are not provided in the paper.
