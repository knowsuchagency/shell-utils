# Description

The `shell_utils` library provides some handy utilities for when you need to automate certain processes using shell commands.

Where you might otherwise write a bash script or muck around with the `subprocess`, `os`, and `sys`  modules in a Python script `shell_utils` provides
some patterns and shortcuts for your automation scripts.

Let's say we have a new project we need to automate some build process(es) for. We might be tempted to write a Makefile or bash
script(s) to help with that task. If that works for you, great. However, if you're like me, you prefer to python-all-the-things.

We can use shell-utils to create an automation script that will behave much the same way a Makefile would, but with all the
Python goodness we want.

Some familiarity with the `click` library will be helpful.

```bash
pip3 install shell_utils
shell_utils generate_runner
```

This will produce an executable python script with the following code
```python
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

    if root != cwd:
        click.secho(f'Navigating from {cwd} to {root}', fg='yellow')
        os.chdir(root)


if __name__ == '__main__':
    main()
```

Now let's say that we're using sphinx to generate the documentation we have in our project's `docs` directory.

If we wanted to create a command that would re-generate our documentation and open a browser window when it's finished,

we could add the following code to our generated `run.py` script


```python
@main.command()
@click.option('--no-browser', is_flag=True, help="Don't open browser after building docs.")
def docs(no_browser):
    """
    Generate Sphinx HTML documentation, including API docs.
    """
    shell(
        """
        rm -f docs/shell_utils.rst
        rm -f docs/modules.rst
        rm -rf docs/shell_utils*
        sphinx-apidoc -o docs/ shell_utils
        """
    )

    with cd('docs'):
        shell('make clean')
        shell('make html')

    shell('cp -rf docs/_build/html/ public/')

    if no_browser:
        return

    shell('open public/index.html')
```

Then, we can execute the following command to do what we intended:

`./run.py docs`

The strings sent to the `shell` function will be executed in a `bash` subprocess shell. Before they are executed,
the `shell` function will print the command to `stdout`, similar to a `Makefile`.

Also, notice we change directories into `docs` using a context manager, that way the commands passed to the `shell` function
will execute within that directory. Once we're out of the context manager's scope, further `shell` function commands are once-again run
from the project root.

# functions and context managers

## shell

Executes the given command in a bash shell. It's just a thin wrapper around `subprocess.run` that adds a couple handy features,
such as printing the command it's about to run to stdout before executing it.

```python
from shell_utils import shell

p1 = shell('echo hello, world')

print(p1)

p2 = shell('echo goodbye, cruel world', capture=True)

print('captured the string:', p2.stdout.decode())
```

**outputs**

```bash
user@hostname executing...

echo goodbye, cruel world


captured the string: goodbye, cruel world
```

## cd

Temporarily changes the current working directory while within the context scope.

Within a python shell...

```python
from shell_utils import shell

shell('echo hello, world')

shell(
    """
    echo foo
    echo bar
    """
)

process = shell('echo aloha', capture=True)

print(f"The last process' stdout was {process.stdout.decode().strip()} and its return code was {process.returncode}")
```

**outputs**

```bash
stephanfitzpatrick@stephanfitzpatrick executing...

echo hello, world

hello, world


stephanfitzpatrick@stephanfitzpatrick executing...


echo foo
echo bar


foo
bar


stephanfitzpatrick@stephanfitzpatrick executing...

echo aloha


The last process' stdout was aloha and its return code was 0
```

## env

Temporarily changes environment variables

```python
from shell_utils import env
import os

print(os.getenv('foo', 'nothing'))

with env(foo='bar'):
    print(os.getenv('foo'))

print(os.getenv('foo', 'nothing again'))
```

**outputs**

```bash
nothing
bar
nothing again
```

## path

A special case of the `env` context manager that alters your $PATH. It expands `~` to your home directory and returns
the elements of the $PATH variable as a list.

```python
from shell_utils import path
import os

def print_path():
    print('$PATH ==', os.getenv('PATH'))

print_path()

with path('~', prepend=True) as plist:
    print_path()
    print(plist)
```

**outputs**

```bash
$PATH == /Users/user/.venvs/shell-utils-py3.7/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Library/TeX/texbin
$PATH == /Users/user:/Users/user/.venvs/shell-utils-py3.7/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/Library/TeX/texbin
['/Users/user', '/Users/user/.venvs/shell-utils-py3.7/bin', '/usr/local/sbin', '/usr/local/bin', '/usr/bin', '/bin', '/usr/sbin', '/sbin', '/Library/TeX/texbin']
```
