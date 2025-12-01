# Python Code Quality Guidelines

This document defines **non-negotiable guardrails** for Python code in this project. The goal is to make the codebase:

* Easy to understand on first read
* Easy to change without fear
* Hard to break accidentally

Assume many engineers will cycle through this project. Your job when writing code is to be a **good ancestor**.

---

## 1. Core Philosophy

1. **Correctness first**

   * A small correct solution beats a clever incomplete one.
   * We prefer obvious, boring code over "smart" tricks.

2. **Functional at the core**

   * Data in → data out, with minimal side effects.
   * Side effects are isolated at the edges (I/O, network, UI).

3. **Strict typing**

   * All public and most internal interfaces are fully typed.
   * Type errors are treated as build failures.

4. **Low lexical and structural complexity**

   * Small functions, shallow nesting, short modules.
   * No "god functions", no "god objects".

5. **Idiomatic Python**

   * Use the common patterns the Python community expects.
   * Avoid re-implementing standard library features.

6. **Consistency over preference**

   * Follow project conventions even if you disagree with them.
   * If you want to change a convention, propose it; don't fork it.

---

## 2. Language Subset and Style

### 2.1 Allowed language features

* Python 3 only, pinned version as per project.
* Use dataclasses or simple classes for data structures.
* Use enums for discrete sets of related values.
* Use comprehensions where they are obviously readable.
* Use context managers for resources (files, locks, DB sessions).

### 2.2 Discouraged / forbidden patterns

* Deep inheritance hierarchies (prefer composition).
* Metaclasses, implicit magic, runtime monkey-patching.
* Global mutable state (singletons, module-level caches) unless explicitly approved.
* Overloaded operator abuse that obscures intent.
* Highly nested comprehensions; if it's not trivial, use a loop.
* Catch-all exception handlers (bare `except` in your head, even if not literally written).

---

## 3. Functional Paradigms

We are not writing pure functional Python, but we lean that way to keep code predictable.

### 3.1 Design

* Prefer:

  * Small, pure functions that transform data.
  * Functions that receive all their inputs via parameters.
  * Functions that return new data instead of mutating arguments.

* Avoid:

  * Functions that implicitly read from or write to global state.
  * Functions that both compute and perform I/O; separate orchestration from logic.

### 3.2 Side-effect boundaries

* Centralize side effects in clearly named layers/modules:

  * `infrastructure` or `adapters` for network, filesystem, databases, etc.
  * `services` for domain logic that orchestrates pure functions + side-effecting adapters.

* Rule of thumb:

  * Most unit tests should not require network, filesystem, or environment variables.
  * If a function is hard to test without heavy mocking, it likely mixes concerns.

### 3.3 Immutability bias

* Prefer:

  * Immutable data structures (tuples, frozensets) when appropriate.
  * Avoid in-place mutation unless it is clearly local and performance-critical.
* Shared data should be treated as immutable; copy before modifying.

---

## 4. Strict Typing

Static typing is mandatory, not optional.

### 4.1 Requirements

* Every function and method:

  * Has explicit type hints for all parameters and return values.
  * Uses typed collections (list[int], dict[str, Any], etc.).
* All class attributes are typed, either via:

  * Dataclasses with annotated fields.
  * Explicit type annotations on attributes in regular classes.

### 4.2 Type checking

* The project uses a strict static type checker (e.g., mypy or pyright):

  * The type checker must pass with zero errors for:

    * All source directories.
    * All tests.
  * No "ignore" directives unless:

    * There is a linked issue explaining why.
    * There is a comment describing a path to remove the ignore.

### 4.3 Type design rules

* Prefer:

  * Narrow, precise types over `Any`.
  * Typed aliases for complex types.
* Avoid:

  * `Any`, `object`, or massive union types unless unavoidable.
  * Generic over-engineering; introduce generics only when actually reused.

---

## 5. Low Lexical and Structural Complexity

### 5.1 Function complexity limits

Per function/method:

* Maximum cyclomatic complexity: 10
* Maximum nesting depth (if/for/while/try): 3 levels
* Maximum function length: 50–60 lines (including blank lines)
* Maximum number of parameters: 5 (excluding `self`/`cls`)

If you hit these limits:

* Split the function into smaller helpers.
* Extract logic into separate, named functions or objects.

### 5.2 Module / file complexity limits

Per module/file:

* Maximum file length: ~400 lines (soft limit).
* Prefer small modules with cohesive responsibilities.
* If a file feels like a "grab bag", split it.

### 5.3 Lexical complexity rules

* Keep the number of local variables in a function low; prefer introducing small helpers.
* Avoid:

  * Long, compound boolean expressions without intermediate naming.
  * Nested lambdas; use named functions instead.
* Use meaningful, full-word names (no "x1", "tmp2", etc.) unless in tiny, obvious scopes.

---

## 6. Idiomatic Python

### 6.1 Naming and structure

* Modules, packages: lowercase_with_underscores.
* Classes: PascalCase.
* Functions and methods: lowercase_with_underscores.
* Constants: UPPERCASE_WITH_UNDERSCORES.

### 6.2 Control flow

* Prefer early returns to reduce nesting.
* Avoid clever one-liners when they obscure logic.
* Use standard idioms:

  * `for` loops instead of manual index counters when possible.
  * `enumerate` and `zip` when they clarify intent.

### 6.3 Data handling

* Use built-in types and the standard library before introducing third-party helpers.
* Prefer explicit over implicit:

  * Explicit conversions instead of relying on coercion.
  * Explicit keyword arguments for critical parameters.

---

## 7. Pre-Build Quality Pipeline

Every commit must pass these checks:

### 7.1 Code formatting

* Use Black with project configuration
* Format on save

### 7.2 Linting

* Use Ruff with strict configuration
* No disabled rules without justification
* Treat warnings as errors in CI

### 7.3 Type checking

* `mypy --strict` or `pyright` must pass with zero errors
* No `# type: ignore` without linked issue

### 7.4 Complexity analysis

* Use radon/xenon to enforce thresholds
* Cyclomatic complexity max: 10 per function

### 7.5 Pre-commit workflow

```bash
ruff check .       # Linting
ruff format .      # Formatting
mypy .             # Type checking
pytest             # Tests
```

---

## 8. Code Review Standards

### 8.1 Reviewer checklist

* Correctness: Does it do what it claims?
* Simplicity: Could this be simpler?
* Types: Are types precise and minimal?
* Tests: Are there tests for new behavior?

### 8.2 Reviewer authority

* Push back on unnecessary complexity
* Require tests for non-trivial changes
* "It works" is not sufficient justification

---

## 9. Cultural Rules

* No unreviewed "quick hacks"
* Prefer "make it simple first" over "optimize prematurely"
* Write code your future self can understand
* When unsure, choose the simpler option
