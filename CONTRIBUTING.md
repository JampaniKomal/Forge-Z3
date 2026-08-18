# Contributing to Forge-Z3

Thank you for considering contributing to Forge-Z3! This document outlines the guidelines for contributing.

## Getting Started

1. Fork the repository.
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/Forge-Z3.git
   cd Forge-Z3
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate       # Windows
   source venv/bin/activate    # Linux/Mac
   pip install -r requirements.txt
   ```
4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Code Standards

### Python Style
- Python 3.10+ required.
- Type hints on all function signatures.
- Docstrings on all public functions and classes (Google style).
- Maximum line length: 100 characters.

### Data Validation
- All external data (LLM outputs, user inputs, file reads) must be validated through **Pydantic v2** schemas.
- Never trust raw strings from any external source.

### Security
- **No `eval()`, `exec()`, or `shell=True` in subprocess calls.** Ever.
- API keys must be loaded from environment variables or `.env` files, never hardcoded.
- Read `SECURITY.md` for the full security policy.

### Testing
- Every new module must include corresponding unit tests in `tests/`.
- Run the full test suite before submitting:
  ```bash
  python -m pytest tests/ -v
  ```
- Run the security linter before submitting:
  ```bash
  bandit -r src/ -ll
  ```

## Commit Messages
Follow the [Conventional Commits](https://www.conventionalcommits.org/) standard:
- `feat:` — A new feature
- `fix:` — A bug fix
- `docs:` — Documentation changes
- `test:` — Adding or updating tests
- `refactor:` — Code restructuring without behavior change
- `chore:` — Maintenance tasks (deps, CI, etc.)

Example: `feat: add Datalog translator for network edges`

## Pull Request Process
1. Ensure all tests pass.
2. Ensure `bandit` reports no high-severity findings.
3. Update `devlog/DEVLOG.md` if your change is significant.
4. Submit a pull request with a clear description of what changed and why.
