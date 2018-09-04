"""
Usage:  [OPTIONS] COMMAND [ARGS]...

  A cli for shell-utils.

Options:
  --help  Show this message and exit.
"""
import sys
import subprocess as sp

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


def invoke_runner():
    """
    This invokes the run.py script in the current directory.
    """
    if not Path(Path(), 'run.py').exists():
        raise SystemExit(
            click.secho('run.py not found in current directory', fg='red')
        )

    sp.run(['python3', 'run.py'] + sys.argv[1:])


if __name__ == "__main__":
    cli()
