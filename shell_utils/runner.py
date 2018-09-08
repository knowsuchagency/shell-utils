#!/usr/bin/env python3
import os
from pathlib import Path

from shell_utils import shell, cd, env, path, quiet, notify, notice

import click

PROJECT_ROOT = Path(__file__).parent.resolve()


@click.group()
def main():
    """
    Development tasks; programmatically generated
    """

    # ensure we're running commands from project root

    cwd = Path().resolve()

    if cwd != root:
        click.secho(f'Navigating from {cwd} to {root}',
                    fg='yellow')
        os.chdir(root)


if __name__ == '__main__':
    main()
