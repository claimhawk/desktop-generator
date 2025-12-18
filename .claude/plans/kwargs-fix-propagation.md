# Plan: kwargs Fix Propagation to Other Generators

**Created**: 2025-12-18
**Related Research**: [../research/kwargs-fix-propagation.md](../research/kwargs-fix-propagation.md)
**Related Todos**: [../todos/kwargs-fix-propagation.md](../todos/kwargs-fix-propagation.md)

## Objective

Propagate the `**_kwargs: object` fix from desktop-generator to all other generators in the ecosystem.

## Approach

Use inter-agent communication protocol: write instruction files to each target project's `.claude/communication/` directory. Individual project agents will execute the fix.

## Execution Steps

### Step 1: Create communication file for account-screen-generator
- **Target**: `account-screen-generator/.claude/communication/from-desktop-generator-20251218.md`
- **Content**: Instructions to add `**_kwargs: object` to `AccountScreenState.generate()`
- **Location**: state.py line 284 (after `num_log_entries` param)

### Step 2: Create communication file for appointment-generator
- **Target**: `appointment-generator/.claude/communication/from-desktop-generator-20251218.md`
- **Location**: state.py line ~292

### Step 3: Create communication file for calendar-generator
- **Target**: `calendar-generator/.claude/communication/from-desktop-generator-20251218.md`
- **Location**: state.py line ~150

### Step 4: Create communication file for chart-screen-generator
- **Target**: `chart-screen-generator/.claude/communication/from-desktop-generator-20251218.md`
- **Location**: state.py line ~333

### Step 5: Create communication file for claim-window-generator
- **Target**: `claim-window-generator/.claude/communication/from-desktop-generator-20251218.md`
- **Location**: state.py line ~136

### Step 6: Create communication file for login-window-generator
- **Target**: `login-window-generator/.claude/communication/from-desktop-generator-20251218.md`
- **Location**: state.py line ~70

## Communication File Template

Each file will contain:
1. Context: Why this fix is needed
2. Reference: Link to desktop-generator commit showing the fix
3. Exact change: Before/after code diff
4. Verification: How to confirm the fix works

## Success Criteria

- All generators accept unknown kwargs without TypeError
- All generators pass ruff and mypy checks
- Workflow can pass `task_type` and other params to any generator
