"""
Usage:  [OPTIONS] COMMAND [ARGS]...

  A cli for shell-utils.

Options:
  --help  Show this message and exit.
"""
from pathlib import Path

from shell_utils import shell

import click


@click.group()
def cli():
    """A cli for shell_utils."""
    pass


@cli.command()
def generate_runner():
    """Generate a run.py script in the current directory."""
    from shell_utils import runner

    runner_path = Path('run.py')

    if runner_path.exists():
        raise EnvironmentError('run.py already exists in current directory')

    click.secho('writing content to run.py', fg='yellow')

    runner_path.write_text(Path(runner.__file__).read_text())

    shell('chmod +x run.py')


if __name__ == "__main__":
    cli()
