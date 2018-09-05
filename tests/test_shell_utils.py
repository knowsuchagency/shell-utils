#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `shell_utils` package."""
from shell_utils.shell_utils import shell, env, path, cd

import pytest


def test_shell_capture():
    """Test shell output capture."""

    string = 'hello'

    echo_string = shell(f'echo {string}', capture=True)

    assert echo_string.returncode == 0
    assert echo_string.raw_stdout.decode().strip() == string
    assert echo_string.stdout.strip() == string

    to_stderr = shell(f'echo "{string}" >&2', capture=True)

    assert to_stderr.returncode == 0
    assert to_stderr.raw_stderr.decode().strip() == string
    assert to_stderr.stderr.strip() == string


def test_shell_raises():
    """Test shell raises."""
    import subprocess as sp

    with pytest.raises(sp.CalledProcessError):
        shell('exit 1')

    assert not shell('exit 1', check=False)


def test_env():
    """Test env context manager."""
    import os
    import copy

    original_env = copy.deepcopy(os.environ)
    string = 'world'

    with env(hello=string):
        assert os.environ['hello'] == string

    assert 'hello' not in os.environ
    assert os.environ == original_env


def test_path():
    """Test path context manager."""
    from pathlib import Path
    from tempfile import TemporaryDirectory
    import os

    original_path = Path(os.environ['PATH'])

    with TemporaryDirectory() as temp_dir, path(temp_dir) as new_path:
        temp_dir = Path(temp_dir)

        assert new_path[-1] == temp_dir.__fspath__()
        assert Path(os.environ['PATH']) != original_path

    assert Path(os.environ['PATH']) == original_path


def test_cd():
    from pathlib import Path

    root = Path().parent.resolve()
    original_cwd = Path().resolve()
    with cd(root):
        assert Path().resolve() == root
    assert Path().resolve() == original_cwd
