# Implementation Plan: Fix Taskbar and Load-Wait Task Failures

**Date:** 2025-12-17
**Related Research:** [../research/20251217-taskbar-loadwait-failures.md](../research/20251217-taskbar-loadwait-failures.md)
**Related Todos:** [../todos/20251217-fix-taskbar-loadwait.md](../todos/20251217-fix-taskbar-loadwait.md)

---

## Problem Summary

| Task                | Accuracy | Root Cause |
|---------------------|----------|------------|
| dclick-desktop-icon | 100%     | Working correctly |
| dclick-taskbar-icon | 0%       | Training/test image dimension mismatch |
| load-wait           | 0%       | Coordinate mismatch + unclear task semantics |

---

## Analysis of Current Implementation

### Taskbar Icons Issue

**Training path (`iconlist_task.py` lines 97-109):**
1. Full image rendered (1920x1080)
2. Image cropped to taskbar bbox (688x47)
3. Coordinates adjusted relative to crop: `rel_x = abs_x - crop_x`
4. RU calculated on cropped dimensions: `ru = (rel / cropped_dim) * 1000`
5. Training sample uses cropped image

**Test path (inherited from `IconListTaskBase`):**
- Likely uses full-screen images but cropped coordinates
- Need to verify by checking cudag base class

### Wait/Loading Issue

**Current design (`wait_loading.py`):**
- Uses click prompts: "Double click the recycle bin icon..."
- Expects wait action: `{"action": "wait", "time": 3.0}`
- Sets `pixel_coords=(0, 0)` for all samples
- Sets `tolerance=(0, 0)`

**Problem:** The prompt-action mismatch is intentional to teach "when loading visible → wait, don't click." However:
1. This requires visual recognition of loading indicator
2. Zero tolerance provides no training signal for spatial grounding
3. Model may not have enough signal to learn this pattern

---

## Proposed Fixes

### Fix 1: Taskbar Icons - Use Full-Screen Images with Full-Screen Coordinates

**Rationale:** Consistency with desktop icons. The model should learn to click taskbar icons on full-screen images, same as desktop icons.

**Changes to `iconlist_task.py`:**
1. Remove per-element cropping logic for taskbar
2. Use full-screen image for all iconlist samples
3. Calculate coordinates relative to full image dimensions
4. Set tolerance to match full screen proportionally

**Alternative considered:** Keep cropped images but ensure test uses same crop. Rejected because:
- Desktop uses full-screen, would create inconsistency
- Harder to debug coordinate issues
- User will see full-screen in production

### Fix 2: Wait/Loading - Improve Training Signal

**Option A: Use wait-specific prompts (RECOMMENDED)**
Instead of "Double click X", use prompts that acknowledge loading:
- "The application is loading. What action should you take?"
- "A loading indicator is visible. What should you do?"
- "Wait for the loading panel to complete before clicking"

**Option B: Add visual grounding for loading indicator**
- Include loading indicator coordinates in metadata
- Model learns to detect loading indicator

**Option C: Hybrid approach**
- Mix click prompts with wait prompts
- Include `od_loading_visible: true` in prompt context

**Recommendation:** Option A - clearer training signal without complex changes.

---

## Implementation Steps

### Step 1: Verify cudag base class behavior
- Read `cudag/core/iconlist_task.py` to understand test generation
- Confirm if test images use full-screen or cropped images

### Step 2: Fix `iconlist_task.py`
- Modify `generate_samples()` to use full-screen images
- Remove element-based cropping for training samples
- Update coordinate calculation to use full image dimensions
- Ensure tolerance reflects full-screen icon bounds

### Step 3: Fix `wait_loading.py`
- Create wait-specific prompts that acknowledge loading state
- Optionally include loading indicator metadata
- Consider if coordinates should point to loading indicator or stay at (0,0)

### Step 4: Update `api.py`
- Align `_generate_iconlist_samples()` with task changes
- Align `_generate_wait_samples()` with task changes

### Step 5: Validate changes
- Run generator to produce test dataset
- Manually inspect samples for correct coordinates
- Run `cudag validate` on generated dataset

---

## File Changes Summary

| File | Changes |
|------|---------|
| `tasks/iconlist_task.py` | Remove cropping, use full-screen coords |
| `tasks/wait_loading.py` | Add wait-specific prompts |
| `api.py` | Align with task file changes |
| `config/dataset.yaml` | May need sample count adjustments |

---

## Verification Checklist

- [ ] Training images match test images (both full-screen)
- [ ] RU coordinates calculated correctly for 1920x1080
- [ ] Tolerance values appropriate for full-screen
- [ ] Wait prompts clearly indicate loading state
- [ ] `cudag validate` passes on generated dataset
- [ ] Visual inspection confirms correct target locations

---

## Rollback Plan

If changes break desktop icons (currently 100%):
1. Revert to previous commit
2. Only apply wait_loading.py changes
3. Investigate taskbar separately
