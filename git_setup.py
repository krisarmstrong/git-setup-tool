#!/usr/bin/env python3
"""
Project Title: Git Setup Tool

Initializes a Git repository and creates standard project files.

Supports dynamic creation of .gitignore, README.md, CHANGELOG.md, requirements.txt, LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, and optionally version_bumper.py, with initial commit and tag. Skips existing files to prevent overwriting and checks for sensitive data before committing.

Author: Kris Armstrong
"""
__version__ = "1.0.4"

import os
import sys
import argparse
import subprocess
import logging
import re
from logging.handlers import RotatingFileHandler
import requests
from pathlib import Path
from typing import Optional

def setup_logging(verbose: bool, logfile: Optional[str] = None) -> None:
    """Configure logging with console and rotating file handler.

    Args:
        verbose: Enable DEBUG level logging if True.
        logfile: Path to log file, defaults to 'git_setup.log' if unspecified.

    Returns:
        None
    """
    logger = logging.getLogger()
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(ch)
    logfile = logfile or 'git_setup.log'
    fh = RotatingFileHandler(logfile, maxBytes=10_000_000, backupCount=5)
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(fh)

def run_cmd(cmd: list[str], cwd: str | Path) -> None:
    """Run a shell command with error handling.

    Args:
        cmd: List of command arguments.
        cwd: Working directory for the command.

    Raises:
        subprocess.CalledProcessError: If the command fails.
    """
    logging.debug("Running command: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True, text=True)

def create_file(path: str | Path, content: str) -> None:
    """Create a file with content if it doesn't exist.

    Args:
        path: Path to the file.
        content: Content to write.

    Returns:
        None
    """
    path = Path(path)
    if path.exists():
        logging.info("%s exists, skipping", path)
    else:
        path.write_text(content)
        logging.info("Created %s", path)

def check_sensitive_data(repo_dir: Path) -> bool:
    """Check for sensitive data in files before committing.

    Args:
        repo_dir: Path to the project directory.

    Returns:
        bool: True if no sensitive data found, False otherwise.
    """
    sensitive_patterns = [r'api_key\s*=\s*["\'].+["\']', r'password\s*=\s*["\'].+["\']']
    for file in repo_dir.rglob('*.py'):
        if file.is_file():
            content = file.read_text()
            for pattern in sensitive_patterns:
                if re.search(pattern, content):
                    logging.warning(f"Potential sensitive data found in {file}")
                    return False
    return True

def check_github_repo(repo_name: str, token: Optional[str]) -> bool:
    """Check if a GitHub repository exists; create it if not.

    Args:
        repo_name: Name of the repository (e.g., 'user/repo').
        token: GitHub personal access token, if provided.

    Returns:
        bool: True if repo exists or was created, False on failure.
    """
    headers = {'Authorization': f'token {token}'} if token else {}
    url = f"https://api.github.com/repos/{repo_name}"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            logging.info("Repository %s exists", repo_name)
            return True
        elif response.status_code == 404 and token:
            create_url = "https://api.github.com/user/repos"
            payload = {"name": repo_name.split('/')[-1], "private": False}
            create_response = requests.post(create_url, headers=headers, json=payload)
            if create_response.status_code == 201:
                logging.info("Created repository %s", repo_name)
                return True
            logging.error("Failed to create repository: %s", create_response.text)
            return False
        logging.error("Repository check failed: %s", response.text)
        return False
    except requests.RequestException as e:
        logging.error("GitHub API error: %s", e)
        return False

def main() -> None:
    """Initialize a Git repository with standard files and optional GitHub setup."""
    parser = argparse.ArgumentParser(
        description="Initialize a Git repo with standard files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--dir', '-d', default=os.getcwd(),
                        help='Directory to initialize')
    parser.add_argument('--remote', '-r', help='Remote repository URL')
    parser.add_argument('--github-repo', help='GitHub repo (e.g., user/repo)')
    parser.add_argument('--github-token', help='GitHub personal access token')
    parser.add_argument('--project-name', default='Project Title',
                        help='Name of the project')
    parser.add_argument('--author', default='Your Name',
                        help='Author name for files')
    parser.add_argument('--commit-message', default='Initial project setup',
                        help='Initial commit message')
    parser.add_argument('--include-bump', action='store_true',
                        help='Include version_bumper.py in project root')
    parser.add_argument('--logfile', '-l', help='Log file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    setup_logging(args.verbose, args.logfile)
    repo_dir = Path(args.dir).absolute()

    try:
        if not (repo_dir / '.git').is_dir():
            run_cmd(['git', 'init'], repo_dir)
            logging.info("Initialized empty Git repository")
        else:
            logging.info("Git repository already initialized")

        if args.github_repo:
            if check_github_repo(args.github_repo, args.github_token):
                remote_url = f"https://github.com/{args.github_repo}.git"
                try:
                    run_cmd(['git', 'remote', 'add', 'origin', remote_url], repo_dir)
                    logging.info("Added remote origin %s", remote_url)
                except subprocess.CalledProcessError:
                    logging.info("Remote origin already set or failed to add")
            else:
                logging.error("GitHub repository setup failed")
                sys.exit(1)

        create_file(repo_dir / '.gitignore', """# Python
__pycache__/
*.py[cod]
*$py.class
# Distribution
build/
dist/
*.egg-info/
# Virtual environments
env/
venv/
.venv/
.env/
# Logs
*.log
# IDE
.vscode/
.idea/
# OS
.DS_Store
# Project-specific
tests/output/
""")

        create_file(repo_dir / 'README.md', f"""# {args.project_name}

A brief description of the project.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py
```
""")

        create_file(repo_dir / 'CHANGELOG.md', f"""# Changelog

## [0.1.0] - Initial Release
- Initial project setup by {args.author}
""")

        create_file(repo_dir / 'requirements.txt', """# Project requirements
""")

        create_file(repo_dir / 'LICENSE', f"""MIT License

Copyright (c) 2025 {args.author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""")

        create_file(repo_dir / 'CONTRIBUTING.md', """# Contributing

We welcome contributions!

1. Fork the repo
2. Create a branch (`git checkout -b feature/your-feature`)
3. Make your changes with tests and doc updates
4. Commit (`git commit -m "feat: description"`) and push
5. Open a pull request against `main`
""")

        create_file(repo_dir / 'CODE_OF_CONDUCT.md', """# Contributor Covenant Code of Conduct

## Our Pledge
We pledge to make participation in our community a harassment-free experience for everyone.

## Our Standards
Examples of positive behavior:
- Demonstrating empathy and kindness
- Respecting differing opinions
- Accepting constructive feedback
- Focusing on community benefit

Examples of unacceptable behavior:
- Sexualized language or advances
- Trolling or insults
- Harassment
- Publishing private information

## Enforcement Responsibilities
Community leaders will clarify and enforce standards, taking fair corrective action.

## Scope
This Code applies within all community spaces and when representing the community publicly.

## Enforcement
Report issues to kris.armstrong@example.com. All complaints will be reviewed fairly.

## Enforcement Guidelines
1. **Correction**: Private warning for inappropriate behavior.
2. **Warning**: Consequences for continued violations.
3. **Temporary Ban**: Ban for serious violations.
4. **Permanent Ban**: Ban for repeated or severe violations.

## Attribution
Adapted from Contributor Covenant v2.1 (https://www.contributor-covenant.org).
""")

        tests_dir = repo_dir / 'tests'
        tests_dir.mkdir(exist_ok=True)
        create_file(tests_dir / 'test_placeholder.py', """#!/usr/bin/env python3

"""
Placeholder test file.
"""
pass
""")

        if args.include_bump:
            create_file(repo_dir / 'version_bumper.py', """#!/usr/bin/env python3
"""
Project Title: Version Bumper

Scans source files for semantic version strings and bumps major, minor, or patch segments.

Supports Git commit and tagging, with configurable regex patterns and directory exclusions.

Author: Kris Armstrong
"""
__version__ = "1.0.0"

import os
import re
import sys
import argparse
import subprocess
import logging
from typing import Optional

def setup_logging(verbose: bool) -> None:
    """Configure logging output.

    Args:
        verbose: Enable DEBUG level logging if True.

    Returns:
        None
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s')

def find_files(root: str, exclude_dirs: list[str]) -> list[str]:
    """Yield Python files under root, skipping exclude_dirs.

    Args:
        root: Root directory to search.
        exclude_dirs: Directories to exclude.

    Returns:
        List of file paths.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for f in filenames:
            if f.endswith('.py'):
                yield os.path.join(dirpath, f)

def bump_version_in_file(path: str, pattern: str, bump_type: str, dry_run: bool) -> Optional[str]:
    """Read file, bump version per pattern, and write back if changed.

    Args:
        path: Path to the file.
        pattern: Regex pattern to find version string.
        bump_type: Version segment to bump ('major', 'minor', 'patch').
        dry_run: Show changes without writing if True.

    Returns:
        New version string if changed, None otherwise.
    """
    text = open(path, 'r').read()
    match = re.search(pattern, text)
    if not match:
        return None
    old_ver = match.group(1)
    major, minor, patch = map(int, old_ver.split('.'))
    if bump_type == 'major':
        major += 1; minor = 0; patch = 0
    elif bump_type == 'minor':
        minor += 1; patch = 0
    else:
        patch += 1
    new_ver = f"{major}.{minor}.{patch}"
    new_text = re.sub(pattern, f'__version__ = "{new_ver}"', text)
    if new_text != text:
        logging.info("Bumping %s: %s -> %s", path, old_ver, new_ver)
        if not dry_run:
            open(path, 'w').write(new_text)
    return new_ver if new_text != text else None

def git_commit_and_tag(project: str, version: str, message: str, dry_run: bool) -> None:
    """Git add, commit, and tag the new version.

    Args:
        project: Path to project root.
        version: New version string.
        message: Commit/tag message.
        dry_run: Show actions without executing if True.

    Returns:
        None
    """
    cmds = [
        ['git', 'add', '.'],
        ['git', 'commit', '-m', message.format(version=version)]
    ]
    for cmd in cmds:
        logging.debug("Running %s", cmd)
        if not dry_run:
            subprocess.run(cmd, cwd=project, check=True)
    tag_cmd = ['git', 'tag', '-a', f'v{version}', '-m', message.format(version=version)]
    logging.debug("Running %s", tag_cmd)
    if not dry_run:
        subprocess.run(tag_cmd, cwd=project, check=True)

def main() -> None:
    """Bump version in project files and optionally commit/tag."""
    parser = argparse.ArgumentParser(
        description="Version Bumper - SemVer helper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-p', '--project', default=os.getcwd(),
                        help='Path to project root')
    parser.add_argument('-t', '--type', choices=['major', 'minor', 'patch'], default='patch',
                        help='Version segment to bump')
    parser.add_argument('-f', '--find-pattern',
                        default=r'__version__\\s*=\\s*["\'](\\d+\\.\\d+\\.\\d+)["\']',
                        help='Regex to locate version string')
    parser.add_argument('-c', '--commit', action='store_true', help='Commit bump to Git')
    parser.add_argument('-g', '--git-tag', action='store_true', help='Create Git tag')
    parser.add_argument('-m', '--message', default='chore: bump version to {version}',
                        help='Commit/tag message format')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    parser.add_argument('--exclude', default='.git,env,venv,.venv,.env,.idea,.vscode',
                        help='Comma-separated dirs to skip')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()
    setup_logging(args.verbose)

    exclude_dirs = args.exclude.split(',')

    new_version = None
    for file in find_files(args.project, exclude_dirs):
        result = bump_version_in_file(file, args.find_pattern, args.type, args.dry_run)
        if result:
            new_version = result

    if new_version:
        logging.info("New version: %s", new_version)
        if args.commit or args.git_tag:
            git_commit_and_tag(args.project, new_version, args.message, args.dry_run)
    else:
        logging.info("No version string found or no change needed.")

if __name__ == '__main__':
    main()
""")

        if check_sensitive_data(repo_dir):
            run_cmd(['git', 'add', '.'], repo_dir)
            run_cmd(['git', 'commit', '-m', args.commit_message], repo_dir)
            logging.info("Created initial commit")
            run_cmd(['git', 'tag', '-a', 'v0.1.0', '-m', args.commit_message], repo_dir)
            logging.info("Tagged v0.1.0")
        else:
            logging.error("Aborted commit due to potential sensitive data")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        logging.error("Command failed: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Cancelled by user, cleaning up")
        sys.exit(0)
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()