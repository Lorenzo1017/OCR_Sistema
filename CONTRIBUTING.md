# Contributing to OCR_Sistema

Thanks for your interest! Contributions of every kind are welcome: bug fixes, new
features, better classification, support for other languages/OSes, documentation.

## Getting started
1. **Fork** the repository and clone your fork.
2. Set up the development environment:
   ```bash
   cd _engine
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
3. Run the tests (they must pass):
   ```bash
   cd _engine && .venv/bin/python -m pytest tests/ -q
   ```

## Workflow
- Create a descriptive branch: `git checkout -b fix-something`.
- Keep changes **small and focused**; one topic per pull request.
- **Add or update tests** for every behavior change.
- Make sure `pytest` passes and the CI (GitHub Actions) is green.
- Open a **Pull Request** against `main` explaining *what* and *why*.

## Style
- Idiomatic Python, single-responsibility modules (see `_engine/ocrsys/`).
- No unnecessary heavy dependencies.
- Everything must stay **local and cross-platform** (macOS/Linux/Windows): do not
  introduce cloud calls or code specific to a single OS without a fallback.
- Note: the default category tree (`categorie.yaml`) and many user-facing strings
  are in Italian, since the project targets Italian documents. Keep category keys
  and real paths unchanged; new code comments can be in English.

## Contribution ideas
- Improve the classification prompt/heuristics (`classify.py`).
- Extend the default category tree (`categorie.yaml`).
- Support alternative LLM models or additional OCR languages.
- Improve notifications on Linux/Windows.

## Reporting bugs
Open an **Issue** with: steps to reproduce, expected vs actual behavior, your
operating system and versions (`ocr-check` helps). **Do not** attach real personal
documents.

## License
By contributing, you agree that your code is released under the **MIT** license.
