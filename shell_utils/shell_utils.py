# -*- coding: utf-8 -*-

"""Main module."""
import copy
import os
import types
import subprocess as sp
import typing as T
from functools import singledispatch, wraps
from contextlib import contextmanager
from getpass import getuser
from socket import gethostname

import click

Pathy = T.Union[os.PathLike, str]


def shell(command: str,
          check=True,
          capture=False,
          show_command=True) -> sp.CompletedProcess:
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
        show_command: show command being run prefixed by user

    Returns: Completed Process

    """
    user = click.style(getuser(), fg='green')
    hostname = click.style(gethostname(), fg='magenta')

    print()

    if show_command:
        print(f'{user}@{hostname}: {command}')

    try:
        process = sp.run(command,
                         check=check,
                         shell=True,
                         stdout=sp.PIPE if capture else None,
                         stderr=sp.PIPE if capture else None
                         )
    except sp.CalledProcessError as err:
        raise SystemExit(err)

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

    os.environ = original_environment


@contextmanager
def path(*paths: Pathy, prepend=False, expand_user=True) -> T.Iterator[
        T.List[str]]:
    """
    Add the paths to $PATH and yield the new $PATH as a list.

    Args:
        prepend: prepend paths to $PATH else append
        expand_user: expands home if ~ is used in path strings
    """
    paths_list: T.List[Pathy] = list(paths)

    paths_str_list: T.List[str] = []

    for index, _path in enumerate(paths_list):
        if not isinstance(_path, str):
            print(f'index: {index}')
            paths_str_list.append(_path.__fspath__())
        elif expand_user:
            paths_str_list.append(os.path.expanduser(_path))

    original_path = os.environ['PATH'].split(':')

    paths_str_list = paths_str_list + \
        original_path if prepend else original_path + paths_str_list

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


@singledispatch
def notify(message: str, title='run.py'):
    """Mac os pop-up notification."""
    shell(f'terminal-notifier -title {title} -message {message} '
          f'-sound default', capture=True, show_command=False)


@notify.register(types.FunctionType)
def _(func):
    """
    Send notification that task has finished.

    Especially useful for long-running tasks
    """

    @wraps(func)
    def inner(*args, **kwargs):
        result = None
        message = 'Succeeded!'

        try:
            result = func(*args, **kwargs)
        except Exception:
            message = 'Failed'
            raise
        else:
            return result
        finally:
            notify(message, title=getattr(func, '__name__'))

    return inner
