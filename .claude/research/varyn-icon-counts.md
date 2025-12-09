# Research: VaryN Icon Count Issue

## Problem
Generated screenshots show too few icons:
- Only 1 taskbar icon
- Very few desktop icons

## Requirements
- Desktop icons: 60-100% of icons + required
- Taskbar icons: 40-100% of icons + required

## Root Cause Found

In `state.py`, both `_place_desktop_icons` (line 185) and `_place_taskbar_icons` (line 320):

```python
k = rng.randint(0, min(num_optional, len(optional)))
selected_optional = rng.sample(optional, k)
```

This selects between **0** and num_optional, allowing as few as 0 optional icons.

## Solution

Change the minimum from 0 to a percentage-based minimum:
- Desktop: min = 60% of optional icons
- Taskbar: min = 40% of optional icons

```python
# Desktop (60-100%)
min_optional = int(len(optional) * 0.6)
max_optional = len(optional)
k = rng.randint(min_optional, max_optional)

# Taskbar (40-100%)
min_optional = int(len(optional) * 0.4)
max_optional = len(optional)
k = rng.randint(min_optional, max_optional)
```
