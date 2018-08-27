# -*- coding: utf-8 -*-

"""Main module."""
import copy
import os
import subprocess as sp
import textwrap
import types
import typing as T
from contextlib import contextmanager
from getpass import getuser
from socket import gethostname

import click

Pathy = T.Union[os.PathLike, str]


def _bool(self: sp.CompletedProcess) -> bool:
    """
    Return True if return code is zero else false.

    Args:
        self: sp.CompletedProcess

    Returns: True or False

    """
    return self.returncode == 0


def shell(command: str,
          check=True,
          capture=False,
          silent=False,
          dedent=True,
          strip=True,
          **kwargs
          ) -> sp.CompletedProcess:
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
        silent: disable the printing of the command that's being run prior to execution
        dedent: de-dent command string; useful if it's a bash script written within a function in your module
        strip: strip ends of command string of newlines and whitespace prior to execution
        kwargs: passed to subprocess.run as-is

    Returns: Completed Process

    """
    user = click.style(getuser(), fg='green')
    hostname = click.style(gethostname(), fg='blue')

    command = textwrap.dedent(command) if dedent else command
    command = command.strip() if strip else command

    if not silent:
        print(f'{user}@{hostname}',
              click.style('executing...', fg='yellow')
              )
        print(command)
        print(
            click.style(
                ('-' * max(len(l) for l in command.splitlines())
                 if command
                 else ''),
                fg='magenta'
            )
        )
        print()

    process = sp.run(
        command,
        check=check,
        shell=True,
        stdout=sp.PIPE if capture else None,
        stderr=sp.PIPE if capture else None,
        **kwargs
    )

    # override bool dunder method

    process._bool = types.MethodType(_bool, process)
    process.__class__.__bool__ = process._bool

    if capture:
        # decode stderr and stdout
        # keep bytes as raw_{stream}
        process.raw_stdout: bytes = process.stdout
        process.raw_stderr: bytes = process.stderr
        process.stdout: str = process.stdout.decode()
        process.stderr: str = process.stderr.decode()

    return process


@contextmanager
def cd(path_: Pathy):
    """Change the current working directory."""
    cwd = os.getcwd()
    os.chdir(os.path.expanduser(path_))
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


# alias bash

bash = shell

__all__ = [
    'shell',
    'bash',
    'cd',
    'env',
    'path',
    'quiet',
]
