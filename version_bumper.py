#!/usr/bin/env python3
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
                        default=r'__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
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