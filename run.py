#!/usr/bin/env python
"""Task runner for the shell-utils project."""
from tempfile import NamedTemporaryFile
from contextlib import contextmanager
from textwrap import dedent
from pathlib import Path
import subprocess as sp
import typing as T
import copy
import os
import re

import click

Pathy = T.Union[os.PathLike, str]


def shell(command: str, check=True, capture=False) -> sp.CompletedProcess:
    """
    Run the command in a shell.

    !!! Make sure you trust the input to this command !!!

    Args:
        command: the command to be run
        check: raise exception if return code not zero
        capture: if set to True, captures stdout and stderr,
                 making them available as stdout and stderr
                 attributes on the returned CompletedProcess.

                 This also means the command's stdout and stderr won't be
                 piped to FD 1 and 2 by default

    Returns: Completed Process

    """
    user = os.getlogin()
    print(f'{user}: {command}')
    process = sp.run(command,
                     check=check,
                     shell=True,
                     stdout=sp.PIPE if capture else None,
                     stderr=sp.PIPE if capture else None
                     )
    print()
    return process


@contextmanager
def cd(path_: Pathy):
    """Change the current working directory."""
    cwd = os.getcwd()
    os.chdir(path_)
    yield
    os.chdir(cwd)


@contextmanager
def env(**kwargs) -> T.Iterator[os._Environ]:
    """Set environment variables and yield new environment dict."""
    original_environment = copy.deepcopy(os.environ)

    for key, value in kwargs.items():
        os.environ[key] = value

    yield os.environ

    for key in os.environ:
        if key in kwargs and os.environ[key] == kwargs[key]:
            del os.environ[key]
        else:
            os.environ[key] = original_environment[key]


@contextmanager
def path(*paths: Pathy, prepend=False, expand_user=True) -> T.Iterator[T.List[str]]:
    """
    Add the paths to $PATH and yield the new $PATH as a list.

    Args:
        prepend: prepend paths to $PATH else append
        expand_user: expands home if ~ is used in path strings
    """
    paths_list: T.List[Pathy] = list(paths)

    paths_str_list: T.List[str]

    for index, _path in enumerate(paths_list):
        if not isinstance(_path, str):
            paths_str_list[index] = _path.__fspath__()
        elif expand_user:
            paths_str_list[index] = os.path.expanduser(_path)

    original_path = os.environ['PATH'].split(':')

    paths_str_list = paths_str_list + original_path if prepend else original_path + paths_str_list

    with env(PATH=':'.join(paths_str_list)):
        yield paths_str_list


@contextmanager
def quiet():
    """
    Suppress stdout and stderr.

    https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions
    """

    # open null file descriptors
    null_file_descriptors = (
        os.open(os.devnull, os.O_RDWR),
        os.open(os.devnull, os.O_RDWR)
    )

    # save stdout and stderr
    stdout_and_stderr = (os.dup(1), os.dup(2))

    # assign the null pointers to stdout and stderr
    null_fd1, null_fd2 = null_file_descriptors
    os.dup2(null_fd1, 1)
    os.dup2(null_fd2, 2)

    yield

    # re-assign the real stdout/stderr back to (1) and (2)
    stdout, stderr = stdout_and_stderr
    os.dup2(stdout, 1)
    os.dup2(stderr, 2)

    # close all file descriptors.
    for fd in null_file_descriptors + stdout_and_stderr:
        os.close(fd)


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
def test_readme():
    """Test README.rst to ensure it will render correctly in warehouse."""
    shell('python setup.py check -r -s')


@main.command()
def uninstall():
    """Uninstalls all Python dependencies."""

    patt = re.compile(r'\w+=(\w+)')

    packages = []

    for line in sp.run(('pip', 'freeze'), stdout=sp.PIPE).stdout.decode().splitlines():
        if '==' in line:
            package, *_ = line.split('==')

        match = patt.search(line)

        if match:
            *_, package = match.groups()

        packages.append(package)

    stdin = os.linesep.join(packages).encode()

    with NamedTemporaryFile() as fn:
        fn.write(stdin)
        fn.seek(0)
        shell(f'cat {fn.name} | xargs pip uninstall -y')


@main.command()
@click.option('--development/--no-development', default=True, help='install development requirements.')
@click.option('--idempotent/--no-idempotent', default=True, help='uninstall current packages before installing.')
def install(development, idempotent):
    """
    Install Python dependencies.
    """
    click.confirm("Only use this if you're using pipenv "
                  "as your virtualenv and dependency management tool. "
                  "Continue?",
                  abort=True)

    context = click.get_current_context()
    if idempotent:
        context.invoke(uninstall)

    development_flag = '-d' if development else ''

    shell(f'pipenv install {development_flag}')
    shell('pip install -e .[dev]')


@main.command()
def dist():
    """Build source and wheel package."""
    context = click.get_current_context()
    context.invoke(clean, build=True)
    shell('python setup.py sdist')
    shell('python setup.py bdist_wheel')


@main.command()
def release():
    """Package and upload a release to pypi."""
    context = click.get_current_context()

    context.invoke(test_readme)
    context.invoke(tox)
    context.invoke(clean, all=True)
    context.invoke(publish_docs, no_browser=True)

    shell('python setup.py sdist bdist_wheel')
    shell('twine upload dist/*')


def clean_build():
    """Remove build artifacts."""
    click.confirm('This will uninstall the shell_utils cli. '
                  'You may need to run `pip install -e .` to reinstall it. '
                  'Continue?',
                  abort=True)

    shell('rm -fr build/')
    shell('rm -fr dist/')
    shell('rm -rf .eggs/')
    shell("find . -name '*.egg-info' -exec rm -fr {} +")
    shell("find . -name '*.egg' -exec rm -f {} +")


def clean_pyc():
    """Remove Python file artifacts."""
    shell("find . -name '*.pyc' -exec rm -f {} +")
    shell("find . -name '*.pyo' -exec rm -f {} +")
    shell("find . -name '*~' -exec rm -f {} +")
    shell("find . -name '__pycache__' -exec rm -fr {} +")


def clean_test():
    """Remove test and coverage artifacts."""
    shell('rm -fr .tox/')
    shell('rm -f .coverage')
    shell('rm -fr htmlcov/')


@main.command()
@click.option('--pyc', is_flag=True, help=clean_pyc.__doc__)
@click.option('--test', is_flag=True, help=clean_test.__doc__)
@click.option('--build', is_flag=True, help=clean_build.__doc__)
@click.option('--all', is_flag=True, help='Clean all files. This is the default')
def clean(pyc, test, build, all):
    """Remove all build, test, coverage and Python artifacts."""
    fn_flag = (
        (clean_pyc, pyc),
        (clean_test, test),
        (clean_build, build)
    )

    if all or not any((pyc, test, build)):
        clean_pyc()
        clean_test()
        clean_build()
    else:
        for fn, flag in fn_flag:
            if flag:
                fn()


@main.command()
@click.option('--capture/--no-capture', default=False, help='capture stdout')
@click.option('--pdb', is_flag=True, help='enter debugger on test failure')
@click.option('--mypy', is_flag=True, help='type-check source code')
def test(capture, pdb, mypy):
    """
    Run tests quickly with default Python.
    """
    pytest_flags = ' '.join([
        '-s' if not capture else '',
        '--pdb' if pdb else ''
    ])

    shell('py.test tests/' + ' ' + pytest_flags)

    if mypy:
        shell('mypy shell_utils tests/')


@main.command()
def tox():
    """Run tests in isolated environments using tox."""
    shell('tox')


@main.command()
@click.option('--no-browser', is_flag=True, help="Don't open browser after building report.")
def coverage(no_browser):
    """Check code coverage quickly with the default Python."""
    shell('coverage run --source shell_utils -m pytest')
    shell('coverage report -m')
    shell('coverage html')

    if no_browser:
        return

    shell('open htmlcov/index.html')


@main.command()
@click.option('--no-browser', is_flag=True, help="Don't open browser after building docs.")
def docs(no_browser):
    """
    Generate Sphinx HTML documentation, including API docs.
    """
    shell('rm -f docs/shell_utils.rst')
    shell('rm -f docs/modules.rst')
    shell('rm -f docs/shell_utils*')
    shell('sphinx-apidoc -o docs/ shell_utils')

    with cd('docs'):
        shell('make clean')
        shell('make html')

    shell('cp -rf docs/_build/html/ public/')

    if no_browser:
        return

    shell('open public/index.html')


@main.command()
def publish_docs():
    """
    Compile docs and publish to GitHub Pages.

    Logic borrowed from `hugo <https://gohugo.io/tutorials/github-pages-blog/>`
    """

    if shell('git diff-index --quiet HEAD --', check=False).returncode != 0:
        shell('git status')
        raise EnvironmentError('The working directory is dirty. Please commit any pending changes.')

    if shell('git show-ref refs/heads/gh-pages', check=False).returncode != 0:
        # initialized github pages branch
        shell(dedent("""
            git checkout --orphan gh-pages
            git reset --hard
            git commit --allow-empty -m "Initializing gh-pages branch"
            git push gh-pages
            git checkout master
            """).strip())
        print('created github pages branch')

    # deleting old publication
    shell('rm -rf public')
    shell('mkdir public')
    shell('git worktree prune')
    shell('rm -rf .git/worktrees/public/')
    # checkout out gh-pages branch into public
    shell('git worktree add -B gh-pages public gh-pages')
    # generating docs
    context = click.get_current_context()
    context.invoke(docs, no_browser=True)
    # push to github
    with cd('public'):
        shell('git add .')
        shell('git commit -m "Publishing to gh-pages (automated)"', check=False)
        shell('git push origin gh-pages --force')

    remotes = shell('git remote -v', capture=True).stdout.decode()

    match = re.search('github.com:(\w+)/(\w+).git', remotes)

    if match:
        user, repo = match.groups()
        click.secho(f'Your documentation is viewable at '
                    f'https://{user}.github.io/{repo}',
                    fg='green')


@main.command()
def update_vendor():
    """
    Update required vendor libraries."""
    shell('rm -rf .vendor/')
    shell('pip install pipenv --target .vendor')


if __name__ == '__main__':
    main()
