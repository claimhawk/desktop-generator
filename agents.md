# Repository Guidelines

This file provides guidance to AI coding assistants when working with code in this repository.

## Project Overview

This is the Desktop Generator - a screen generator that produces synthetic desktop screenshots for training vision-language models.

## Code Quality

- Target Python 3.12+, four-space indentation, and PEP 8 defaults
- All Python code must pass ruff, mypy, and radon checks
- Maximum cyclomatic complexity: 10
- All functions must have type hints

## Commands

```bash
uv run --python 3.12 python generator.py  # Generate dataset
./scripts/pre-commit.sh --all             # Quality checks
```

## Coordinate System

All coordinates use RU (Resolution Units) normalized to [0, 1000]:
- Conversion: `normalized = (pixel / image_dimension) * 1000`

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
- Training image paths: `images/filename.ext` (relative to dataset root)
- Test screenshot paths: `images/filename.png` (relative to test dir)
- Test directory must be `test/images/`, NOT other names
- All records must include `tolerance` field

Validate with: `cudag validate <dataset_path>`

## Git Commits

**DO NOT CO-AUTHOR COMMITS** - only use the GitHub user's name when committing. Do not add co-author trailers or attribute commits to AI assistants.
