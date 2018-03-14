===========
shell-utils
===========


.. image:: https://img.shields.io/pypi/v/shell_utils.svg
        :target: https://pypi.python.org/pypi/shell_utils

.. image:: https://img.shields.io/travis/knowsuchagency/shell-utils.svg
        :target: https://travis-ci.org/knowsuchagency/shell-utils

.. image:: https://pyup.io/repos/github/knowsuchagency/shell-utils/shield.svg
     :target: https://pyup.io/repos/github/knowsuchagency/shell-utils/
     :alt: Updates

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg



Some helpers to make interacting with the shell easier


* Documentation: https://knowsuchagency.github.io/shell-utils
* Source: https://github.com/knowsuchagency/shell-utils


Installation
------------

    pipenv install shell-utils

Usage
---------

.. code-block:: Python

    def test_shell_capture():
        """Test shell output capture."""

        string = 'hello'

        echo_string = shell(f'echo {string}', capture=True)

        assert echo_string.returncode == 0
        assert echo_string.stdout.decode().strip() == string

        to_stderr = shell(f'echo "{string}" >&2', capture=True)

        assert to_stderr.returncode == 0
        assert to_stderr.stderr.decode().strip() == string


    def test_shell_raises():
        """Test shell raises."""
        import subprocess as sp

        with pytest.raises(sp.CalledProcessError):
            shell('exit 1')

        assert shell('exit 1', check=False).returncode == 1


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
