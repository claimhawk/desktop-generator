# Todo List: Fix Taskbar and Load-Wait Task Failures

**Date:** 2025-12-17
**Related Research:** [../research/20251217-taskbar-loadwait-failures.md](../research/20251217-taskbar-loadwait-failures.md)
**Related Plan:** [../plans/20251217-fix-taskbar-loadwait.md](../plans/20251217-fix-taskbar-loadwait.md)

---

## Status Legend
- [ ] Pending
- [x] Completed
- [>] In Progress

---

## Pre-Implementation

- [ ] Verify cudag IconListTaskBase test generation behavior
- [ ] Confirm test image dimensions vs training image dimensions

---

## Taskbar Icons Fix

- [ ] Modify `iconlist_task.py` to use full-screen images (not cropped)
- [ ] Update coordinate calculation to use full image (1920x1080)
- [ ] Update tolerance to reflect full-screen icon bounds
- [ ] Verify RU conversion is correct for full dimensions

---

## Wait/Loading Fix

- [ ] Create wait-specific prompts in annotation or task code
- [ ] Update `wait_loading.py` to use new prompts
- [ ] Consider adding loading indicator coordinates to metadata
- [ ] Verify prompt clearly indicates loading state

---

## API Alignment

- [ ] Update `_generate_iconlist_samples()` in api.py
- [ ] Update `_generate_wait_samples()` in api.py
- [ ] Ensure both match task file implementations

---

## Validation

- [ ] Generate test dataset
- [ ] Run `cudag validate` on dataset
- [ ] Visual inspection of sample images
- [ ] Verify desktop icons still work (regression test)
- [ ] Check coordinate values in data.jsonl

---

## Post-Implementation

- [ ] Document changes in progress.md
- [ ] Update this todo list with completion status
