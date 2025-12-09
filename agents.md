# Repository Guidelines

This file provides guidance to AI coding assistants when working with code in this repository.

## Project Overview

This is the Desktop Generator — a screen generator that produces synthetic desktop screenshots for training vision-language models.

## Subagent Execution Model (REQUIRED)

All AI assistants **must decompose complex tasks into explicit sub-tasks** and assign each sub-task to an isolated **subagent**. This is mandatory to:

* Prevent uncontrolled context growth
* Ensure deterministic, auditable reasoning
* Preserve repository-wide clarity and focus
* Enforce separation of concerns

### Subagent Requirements

Every non-trivial request (multi-step, multi-file, or multi-decision) must:

1. **Produce a task plan**

   * Break the task into atomic sub-tasks
   * Each sub-task must correspond to a subagent
   * Each subagent must have a clear contract: inputs, outputs, constraints

2. **Run subagents independently**

   * Subagents do not share context except the explicit inputs passed to them
   * Subagents must not add new unrelated context
   * Only the orchestrator (main agent) sees the entire plan

3. **Return a composed final output**

   * The orchestrator integrates the subagents' outputs
   * No subagent should assume global repository state
   * Subagent contamination of context is forbidden

### Subagent Execution Style

Subagents must:

* Operate statelessly
* Use only their given inputs
* Produce minimal, strictly-scoped outputs
* Never rewrite or infer beyond their assigned scope

The orchestrator must:

* Keep reasoning steps isolated
* Avoid long-context carryover
* Enforce strict task boundaries

**If a task does not use subagents for its sub-tasks, it is considered invalid and must be re-executed using the subagent protocol.**

## Three-Step Implementation Protocol (MANDATORY)

All coding tasks must follow a strict three-stage workflow to ensure traceability, clarity of thought, and separation of reasoning, planning, and execution.

### 1. Research Phase → `./.claude/research/<file>`

This file contains all initial thinking, exploration, reasoning, alternatives considered, risks, constraints, and relevant contextual evaluation.

* This stage is for raw cognitive work
* No code allowed
* Subagents may be used to analyze sub-problems
* Output must be structured and comprehensive

### 2. Planning Phase → `./.claude/plans/<file>`

This file contains the **implementation plan only**.

* No code allowed
* Must list steps, modules, functions, structures, data flows, edge cases, test strategies
* Subagents must be used to design and validate individual parts of the plan
* The plan must be deterministic and complete

### 3. Implementation Progress Log → `./.claude/implementation/progress.md`

This file is your "life update" journal for the maintainer.

* Every commit-sized action must be logged
* Summaries of what was done, blockers, decisions
* Subagent invocations must be recorded as separate, timestamped entries

**Coding may only begin after these three steps are complete.**

## Code Quality

* Target Python 3.12+, four-space indentation, and PEP 8 defaults
* All Python code must pass ruff, mypy, and radon checks
* Maximum cyclomatic complexity: 10
* All functions must have type hints

## Commands

```bash
uv run --python 3.12 python generator.py  # Generate dataset
./scripts/pre-commit.sh --all             # Quality checks
```

## Coordinate System

All coordinates use RU (Resolution Units) normalized to [0, 1000]:

* Conversion: `normalized = (pixel / image_dimension) * 1000`

## Dataset Schema

**CRITICAL: Do not modify the dataset filesystem structure or record formats.**

Generated datasets must conform to the CUDAG schema. See `cudag/docs/DATASET_SCHEMA.md` for full details.

Required structure:

```
datasets/{name}/
├── config.json, data.jsonl, train.jsonl, val.jsonl
├── images/           # Training images (*.jpg or *.png)
└── test/
    ├── test.json     # Test cases
    └── images/       # Test screenshots (*.png)
```

Key constraints:

* Training image paths: `images/filename.ext` (relative to dataset root)
* Test screenshot paths: `images/filename.png` (relative to test dir)
* Test directory must be `test/images/`, NOT other names
* All records must include `tolerance` field

Validate with: `cudag validate <dataset_path>`

## Git Commits

**DO NOT CO-AUTHOR COMMITS** — only use the GitHub user's name when committing. Do not add co-author trailers or attribute commits to AI assistants.

---

If you'd like, I can also add small templates for the `research`, `plans`, and `progress.md` files and create them in the repo.
