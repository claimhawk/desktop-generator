# Desktop Generator Development Progress

## Overview
The Desktop Generator is a CUDAG-based screen generator that produces synthetic Windows desktop screenshots for training vision-language models to navigate and interact with desktop environments.

## Development Timeline

| Date | Feature | Work |
|------|---------|------|
| 2025-11-26 | **Project Initialization** | Initial scaffolding from `cudag new` |
| 2025-11-26 | **Desktop Icon Click Tasks** | Implemented desktop icon click tasks with full pipeline |
| 2025-11-27 | **Wait-Loading Task** | Added wait-loading task for OD loading splash screen |
| 2025-12-01 | **Workflow Orchestration** | Updated config and scripts, added workflow orchestration |
| 2025-12-01 | **Contributing Guidelines** | Added contributing section to README |
| 2025-12-01 | **License Update** | Updated license to Tylt proprietary (research use only) |
| 2025-12-02 | **Desktop Icons Fix** | Fixed desktop icons to use double_click instead of left_click |
| 2025-12-02 | **Taskbar Icons Fix** | Fixed taskbar icons to use double_click instead of left_click |
| 2025-12-02 | **Documentation** | Added agents.md with commit guidelines and CLAUDE.md symlink |
| 2025-12-03 | **Metadata Enhancement** | Added tolerance to training sample metadata for all tasks |
| 2025-12-03 | **Dataset Schema Docs** | Added dataset schema documentation to agents.md |
| 2025-12-04 | **Dataset Configuration** | Fixed dataset config: train/val split comment, standardized .researcher |
| 2025-12-04 | **Seed Standardization** | Standardized seed to 420 for reproducibility |
| 2025-12-04 | **Dataset Scaling** | Increased dataset size and adjusted train/val split |
| 2025-12-04 | **Scroll Tasks** | Increased scroll task counts for more training data |
| 2025-12-05 | **Experiment Labeling** | Added --exp argument for experiment labels in dataset naming |
| 2025-12-05 | **Data-Driven Generation** | Refactored to data-driven generation from annotation.json |
| 2025-12-06 | **Icon List Scaling** | Increased iconlist task count to 2000 |
| 2025-12-07 | **Verification Support** | Added verify.py and updated generate.sh with --verify support |

## Feature Categories

### Core Functionality
- **Desktop Icon Clicks** - Double-click tasks for launching applications from desktop icons
- **Taskbar Interaction** - Double-click tasks for taskbar icons
- **Wait-Loading** - Detection and waiting for OD loading splash screen
- **Scrollable Desktop** - Support for desktop with many icons requiring scroll

### Data Generation
- **Annotation-Driven** - Refactored to generate from annotation.json for consistent UI elements
- **Task Diversity** - Icon list, desktop icons, taskbar icons, wait-loading tasks
- **Scaling** - Increased task counts (2000 iconlist tasks, increased scroll tasks)
- **Seed Standardization** - Reproducible generation with seed=420

### Quality & Validation
- **Tolerance Metadata** - Added tolerance field to all training samples
- **Verification** - Added verify.py script for dataset validation
- **Action Correctness** - Fixed double_click vs left_click for desktop/taskbar icons
- **Dataset Schema** - Comprehensive documentation in agents.md

### Infrastructure
- **CUDAG Framework** - Built on CUDAG for declarative screen definitions
- **Workflow Integration** - Config and scripts for workflow orchestration
- **Experiment Tracking** - --exp argument for labeling experimental datasets
- **Train/Val Split** - Proper dataset splitting configuration

### Documentation & Governance
- **Contributing Guidelines** - Clear contribution requirements
- **Code Quality** - Commit guidelines in agents.md
- **Licensing** - Tylt proprietary license (research use only)
- **Dataset Schema** - Full schema documentation for generated datasets

## Current Status

### Dataset Statistics
- **Icon List Tasks**: 2000
- **Desktop Icon Tasks**: Variable based on annotation
- **Taskbar Icon Tasks**: Variable based on annotation
- **Wait-Loading Tasks**: Variable based on annotation
- **Total Estimated Samples**: 18,292+ (from CTO progress report)

### Action Types Supported
1. `double_click` - Desktop icons, taskbar icons
2. `wait` - Loading splash screen detection
3. `scroll` - Desktop scrolling for icon navigation

### Known Configuration
- **Seed**: 420 (standardized)
- **Train/Val Split**: Configured in dataset.yaml
- **Researcher**: Standardized via .researcher file
- **Experiment Labels**: Supported via --exp flag

## Next Steps

### Immediate Priorities
1. Monitor desktop expert model accuracy (currently 100% per CTO report)
2. Continue increasing task diversity for edge cases
3. Add more desktop scenarios (right-click menus, drag-drop)

### Future Enhancements
1. Windows Start Menu navigation
2. File Explorer interactions
3. Multi-monitor desktop scenarios
4. Desktop context menu tasks
5. Drag-and-drop operations

## Technical Debt
- None currently identified - project is well-structured

## Dependencies
- CUDAG framework
- Python 3.12+
- annotation.json for UI element definitions
- Modal for deployment (via parent platform)

## Performance Notes
- Data-driven generation from annotation.json provides consistency
- Seed standardization (420) ensures reproducibility
- Verification script helps catch generation errors early
- 100% accuracy achieved in desktop expert model
