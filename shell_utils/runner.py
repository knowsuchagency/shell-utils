#!/usr/bin/env python3
import os
from pathlib import Path

from shell_utils import shell, cd, env, path, quiet

import click


@click.group()
def main():
    """
    Development tasks; programmatically generated
    """

    # ensure we're running commands from project root

    root = Path(__file__).parent.absolute()
    cwd = Path().absolute()

    if root != cwd:
        click.secho(f'Navigating from {cwd} to {root}',
                    fg='yellow')
        os.chdir(root)


if __name__ == '__main__':
    main()
