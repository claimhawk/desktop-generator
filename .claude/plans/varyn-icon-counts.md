# Plan: Fix VaryN Icon Count Ranges

## Goal
- Desktop icons: 60-100% of optional icons + all required
- Taskbar icons: 40-100% of optional icons + all required

## Changes

### File: `state.py`

#### 1. Update `_place_desktop_icons` (line 182-187)

**Before:**
```python
if vary_n:
    num_optional = max(0, num_icons - len(required))
    k = rng.randint(0, min(num_optional, len(optional)))
    selected_optional = rng.sample(optional, k)
    icon_ids = required + selected_optional
```

**After:**
```python
if vary_n:
    # Select 60-100% of optional icons + all required
    min_optional = int(len(optional) * 0.6)
    max_optional = len(optional)
    k = rng.randint(min_optional, max_optional)
    selected_optional = rng.sample(optional, k)
    icon_ids = required + selected_optional
```

#### 2. Update `_place_taskbar_icons` (line 317-322)

**Before:**
```python
if vary_n:
    num_optional = max(0, num_icons - len(required))
    k = rng.randint(0, min(num_optional, len(optional)))
    selected_optional = rng.sample(optional, k)
    selected = required + selected_optional
```

**After:**
```python
if vary_n:
    # Select 40-100% of optional icons + all required
    min_optional = int(len(optional) * 0.4)
    max_optional = len(optional)
    k = rng.randint(min_optional, max_optional)
    selected_optional = rng.sample(optional, k)
    selected = required + selected_optional
```

## Verification
- Run `./scripts/generate.sh --dry`
- Check generated images for icon counts
- Verify desktop has 60%+ icons, taskbar has 40%+ icons
