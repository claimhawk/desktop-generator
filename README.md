# test-desktop-generator

CUDAG project for generating training data.

## Setup

```bash
pip install -e .
```

## Structure

- `screen.py` - Screen definition (regions, layout)
- `state.py` - State dataclass (dynamic data)
- `renderer.py` - Image rendering logic
- `models/` - Domain model definitions (Patient, Provider, etc.)
- `tasks/` - Task implementations
- `config/` - Dataset configurations
- `assets/` - Base images, fonts, etc.

## Usage

```bash
# Generate dataset
cudag generate --config config/dataset.yaml

# Or run directly
python generate.py --config config/dataset.yaml
```

## Development

1. Edit `screen.py` to define your UI regions
2. Edit `state.py` to define your data model
3. Edit `renderer.py` to implement image generation
4. Add domain models in `models/` for data generation
5. Add tasks in `tasks/` for each interaction type
6. Configure dataset.yaml with sample counts
