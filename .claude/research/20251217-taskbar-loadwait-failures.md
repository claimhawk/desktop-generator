# Research: Model Failures on Taskbar Icons and Load-Wait Tasks

**Date:** 2025-12-17
**Issue:** checkpoint-60 shows 0% accuracy on taskbar icons and load-wait tasks
**Related Plan:** [../plans/20251217-fix-taskbar-loadwait.md](../plans/20251217-fix-taskbar-loadwait.md)
**Related Todos:** [../todos/20251217-fix-taskbar-loadwait.md](../todos/20251217-fix-taskbar-loadwait.md)

---

## Test Results Summary

| Task                | Accuracy       |
|---------------------|----------------|
| dclick-desktop-icon | 100% (67/67)   |
| dclick-taskbar-icon | 0% (0/33)      |
| load-wait           | 0% (0/100)     |

Overall: 33.5% (67/200)

Training metrics show loss converged to 0.0992 at step 60, indicating the model learned *something* - but only desktop icon clicks.

---

## Root Cause Analysis

### 1. Taskbar Icons - Coordinate System Mismatch

**The Problem:**
- Test images are full-screen (1920x1080)
- Coordinates are generated assuming cropped taskbar region (~688x47 pixels)
- Tolerances `[482, 33]` match taskbar dimensions, not full screen

**Code Location:** `tasks/iconlist_task.py`

When generating taskbar samples:
1. Image is cropped to taskbar bounding box (688x47)
2. Coordinates are calculated relative to cropped image
3. RU conversion uses cropped dimensions
4. Test images get full-screen screenshots with these cropped-relative coordinates

**Example Mismatch:**
```
Expected coordinate: [499, 978] (in 1000x1000 RU)
Tolerance: [482, 33]

On full 1920x1080 screen:
  499 RU = 958 pixels from left
  978 RU = 1056 pixels from top (off-screen!)

Actual taskbar location:
  X: ~600-1300 pixels (center of screen)
  Y: ~1033-1080 pixels (bottom strip)
```

The model predicts coordinates for a cropped image but receives full screenshots.

### 2. Load-Wait Tasks - Multiple Structural Issues

**Issue A: Hard-coded Zero Coordinates**
```python
# wait_loading.py lines 122-138
pixel_coords=(0, 0),  # Always 0,0
tolerance=(0, 0),     # No tolerance
```

The model receives `[0, 0]` coordinates for every wait sample, making spatial learning impossible.

**Issue B: Prompt-Action Conflict**
- Prompt: "Double click the recycle bin icon to open recycle bin"
- Expected action: `{"action": "wait", "time": 3.0}`

The model sees "click X" but must output "wait". This contradicts the training signal.

**Issue C: Image Cropping Without Coordinate Adjustment**
- Images cropped to desktop region (1914x1032)
- Ground truth contains icon positions but coordinates set to [0,0]
- No spatial grounding can occur

### 3. Desktop Icons - Why They Work

- Full-screen images (1920x1080)
- Coordinates properly calculated for full image
- Tolerance [1340, 722] spans desktop region correctly
- Prompt matches action: "click X" -> double_click at coordinate

---

## Data Distribution Analysis

**Training set (config/dataset.yaml):**
```yaml
tasks:
  iconlist: 2000  # Split between desktop + taskbar
  wait-loading: 100
```

**Test set distribution:**
- Desktop click: 67 samples (33.5%)
- Taskbar click: 33 samples (16.5%)
- Wait/load: 100 samples (50%)

The model achieved 100% on 33.5% of tests (desktop only).

---

## Files Requiring Changes

1. **`tasks/iconlist_task.py`**
   - Fix coordinate generation for taskbar samples
   - Ensure coordinates match full-screen images or crop consistently

2. **`tasks/wait_loading.py`**
   - Remove hard-coded [0,0] coordinates
   - Fix prompt-action alignment
   - Clarify the task semantics

3. **`api.py`**
   - Review `_generate_iconlist_samples()` coordinate conversion
   - Review `_generate_wait_samples()` implementation

---

## Key Questions to Resolve

1. **For taskbar:** Should we use full-screen images with full-screen coordinates, or cropped images with cropped coordinates?
   - Recommendation: Full-screen images with proper full-screen coordinates for consistency

2. **For wait task:** What is the actual intended behavior?
   - Option A: Model outputs "wait" when loading indicator visible (no coordinates needed)
   - Option B: Model outputs "wait at location" while loading
   - Recommendation: Clarify semantics and fix prompt/action alignment

3. **Coordinate system:** Is there a normalization bug in RU conversion?
   - Need to verify `pixel_to_ru()` and `_convert_bbox_to_ru()` functions

---

## External References

- CUDAG dataset schema: `cudag/docs/DATASET_SCHEMA.md`
- Coordinate system documentation: Uses RU [0, 1000] normalized
- Conversion formula: `ru = (pixel / dimension) * 1000`
