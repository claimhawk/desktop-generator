# Research: kwargs Fix Propagation to Other Generators

**Created**: 2025-12-18
**Related Plan**: [../plans/kwargs-fix-propagation.md](../plans/kwargs-fix-propagation.md)
**Related Todos**: [../todos/kwargs-fix-propagation.md](../todos/kwargs-fix-propagation.md)

## Problem Statement

When workflow passes kwargs to a generator's `State.generate()` method that the method doesn't recognize (like `task_type`), it causes a `TypeError`. This breaks the workflow's ability to pass context parameters to generators.

## Root Cause Analysis

In `cudag/src/cudag/annotation/loader.py`, the loader calls `State.generate()` with various kwargs. If the generate method doesn't accept `**kwargs`, Python raises:
```
TypeError: generate() got an unexpected keyword argument 'task_type'
```

The try/except in loader.py then falls back to `generate(rng)` without important parameters like `od_loading_visible`, breaking functionality.

## Fix Applied in desktop-generator

Commit `50e415d` in desktop-generator added `**_kwargs: object` to accept and ignore unknown kwargs:

```python
# Before (line 91 of state.py)
def generate(
    cls,
    rng: Random,
    num_desktop_icons: int = 5,
    num_taskbar_icons: int = 3,
    od_loading_visible: bool = False,
) -> "DesktopState":

# After
def generate(
    cls,
    rng: Random,
    num_desktop_icons: int = 5,
    num_taskbar_icons: int = 3,
    od_loading_visible: bool = False,
    **_kwargs: object,  # Accept and ignore unknown kwargs
) -> "DesktopState":
```

## Generators Requiring This Fix

| Generator | File | Line | Current Signature |
|-----------|------|------|-------------------|
| account-screen-generator | state.py | 278 | `generate(cls, rng, num_family_members=4, num_account_entries=10, num_log_entries=None)` |
| appointment-generator | state.py | 292 | TBD |
| calendar-generator | state.py | 150 | TBD |
| chart-screen-generator | state.py | 333 | TBD |
| claim-window-generator | state.py | 136 | TBD |
| login-window-generator | state.py | 70 | TBD |

## Implementation Pattern

The fix is consistent across all generators:
1. Add `**_kwargs: object,` as the last parameter before the return type annotation
2. Add comment `# Accept and ignore unknown kwargs`
3. No changes to function body required

## Verification

After fix, generators should:
1. Pass `ruff check state.py`
2. Pass `mypy state.py`
3. Accept arbitrary kwargs without raising TypeError
