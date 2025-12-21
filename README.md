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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes:
   - Generalize hardcoded values rather than replacing them with your own
   - Add tests for new functionality
   - Ensure all quality checks pass
4. Submit a pull request

**Code quality requirements:**
- Lexical complexity checks
- Syntax linting
- Code formatting
- Copyright headers

AI-assisted code is welcome provided it includes tests and passes all checks.

---

<div align="center">

### 🚀 We're Hiring

**ClaimHawk** builds computer-use agents that automate real work using vision-language models.

If you have a passion for machine learning (and some real background) and want to see the path to **100x developer** — we have open intern positions.

**No resumes.** Just shoot an email with your qualifications and passions to:

📧 **hello@claimhawk.app**

</div>
