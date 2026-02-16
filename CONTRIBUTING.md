# Contributing

Thanks for contributing to `ai-cost-tracker`.

## How to report bugs

1. Open a GitHub issue with a minimal reproduction.
2. Include Python version, OS, provider SDK version, and stack trace.
3. Add expected vs actual behavior, plus any relevant logs.

## How to add model support

1. Update `ai_cost_tracker/pricing.py` with the new model and pricing tuple.
2. Add aliases if providers return versioned model names.
3. Add/extend tests in `tests/test_all.py` for exact and partial model resolution.
4. Update `README.md` supported model/provider lists.

## PR process

1. Fork and create a branch (`codex/feature-name` recommended).
2. Add or update tests for behavior changes.
3. Run `pytest` locally.
4. Submit a PR with:
   - summary of changes
   - test evidence
   - any migration notes

## Development setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install package in editable mode:
   ```bash
   pip install -e .
   ```
4. Run tests:
   ```bash
   pytest
   ```
