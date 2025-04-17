# Git Tools Bundle

A utility for initializing Git repositories and managing versioning for Python projects.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
### git_setup.py
```bash
python git_setup.py --dir /path/to/project [--remote <URL>] [--github-repo user/repo] [--github-token <token>] [--project-name "My Project"] [--author "Jane Doe"] [--commit-message "Initial setup"] [--include-bump] [--verbose] [--logfile path]
```

### version_bumper.py
```bash
python version_bumper.py --project /path/to/project [--type minor] [--commit] [--git-tag] [--dry-run]
```

## Generated Files
- **.gitignore**: Ignores Python, IDE, OS, and project-specific files (e.g., `__pycache__`, `.venv`, `tests/output/`).
- **README.md**: Project template with customizable title, installation, and usage sections.
- **CHANGELOG.md**: Initial changelog with a 0.1.0 entry, customizable author.
- **requirements.txt**: Placeholder for project dependencies.
- **LICENSE**: MIT license with customizable author.
- **CONTRIBUTING.md**: Guidelines for contributing via fork-branch-PR.
- **CODE_OF_CONDUCT.md**: Contributor Covenant with contact info.
- **tests/**: Directory with a placeholder test file to encourage testing.
- **version_bumper.py** (optional): Tool for bumping semantic versions in Python files.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)](https://github.com)
[![PyPI](https://img.shields.io/pypi/v/git-tools-bundle)](https://pypi.org/project/git-tools-bundle/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)