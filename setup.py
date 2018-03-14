#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
from setuptools import setup

try:
    import pipenv
except ImportError:
    print('pipenv not installed for current python')
    print('using vendored version in ./.vendor/')
    import sys
    sys.path.append('.vendor')
finally:
    from pipenv.project import Project
    from pipenv.utils import convert_deps_to_pip

# get requirements from Pipfile
pfile = Project(chdir=False).parsed_pipfile
default = convert_deps_to_pip(pfile['packages'], r=False)
development = convert_deps_to_pip(pfile['dev-packages'], r=False)

setup(
    install_requires=default,
    tests_require=development,
    extras_require={
        'dev': development,
        'development': development,
        'test': development,
        'testing': development,
    },
    entry_points={
        'console_scripts': [
            'shell_utils=shell_utils.cli:main'
        ]
    },
)
