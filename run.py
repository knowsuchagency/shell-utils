#!/usr/bin/env python3
"""Task runner for the shell-utils project."""
from tempfile import NamedTemporaryFile
from textwrap import dedent
from pathlib import Path
import subprocess as sp
import os
import re

from shell_utils import shell, cd

import click


@click.group()
def main():
    """
    Development tasks for shell-utils

    """

    # ensure we're running commands from project root

    root = Path(__file__).parent.absolute()
    cwd = Path().absolute()

    if root != cwd:
        click.secho(f'Navigating from {cwd} to {root}',
                    fg='yellow')
        os.chdir(root)


@main.command()
@click.option('--username', '-u', envvar='PYPI_USERNAME')
@click.option('--password', '-p', envvar='PYPI_PASSWORD')
def publish(username, password):
    """
    Build and publish latest version to pypi.
    """
    shell(f'poetry publish --build --username {username} --password {password}')


@main.command()
@click.option('--auto-commit', is_flag=True, help='auto-commit if files changed')
def autopep8(auto_commit):
    """Autopep8 modules."""

    def working_directory_dirty():
        """Return True if the git working directory is dirty."""
        return shell('git diff-index --quiet HEAD --', check=False).returncode != 0

    if auto_commit and working_directory_dirty():
        msg = click.style('working directory dirty. please commit pending changes',
                          fg='yellow')
        raise EnvironmentError(msg)

    shell('autopep8 -i -r shell_utils/ tests/')

    if auto_commit and working_directory_dirty():
        shell('git add -u')
        shell("git commit -m 'autopep8 (autocommit)'", check=False)


@main.command()
@click.option('--mypy', is_flag=True, help='type-check source code')
def tests(mypy):
    """
    Run tests quickly with default Python.
    """

    with cd('tests'):
        shell('pytest', check=False)

    if mypy:
        p = shell('mypy shell_utils tests/ --ignore-missing-imports', check=False, capture=True)
        if p.stdout:
            raise SystemExit(click.secho(p.stdout, fg='red'))


if __name__ == '__main__':
    main()
