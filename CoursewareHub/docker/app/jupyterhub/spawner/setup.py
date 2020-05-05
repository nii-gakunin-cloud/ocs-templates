#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

import os
import sys

v = sys.version_info
if v[:2] < (3,3):
    error = "ERROR: Jupyter Hub requires Python version 3.3 or above."
    print(error, file=sys.stderr)
    sys.exit(1)


if os.name in ('nt', 'dos'):
    error = "ERROR: Windows is not supported"
    print(error, file=sys.stderr)

# At least we're on the python version we need, move on.

from setuptools import setup

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))

from setuptools.command.bdist_egg import bdist_egg
class bdist_egg_disabled(bdist_egg):
    """Disabled version of bdist_egg
    Prevents setup.py install from performing setuptools' default easy_install,
    which it should never ever do.
    """
    def run(self):
        sys.exit("Aborting implicit building of eggs. Use `pip install .` to install from source.")

setup_args = dict(
    name                = 'coursewareuserspawner',
    packages            = ['coursewareuserspawner'],
    version             = '0.1.0',
    description         = """Coursewarespawner: A custom spawner for Jupyterhub.""",
    long_description    = "Spawn single-user servers with Docker.",
    platforms           = "Linux, Mac OS X",
    cmdclass = {
        'bdist_egg': bdist_egg if 'bdist_egg' in sys.argv else bdist_egg_disabled,
    }
)



def main():
    setup(**setup_args)

if __name__ == '__main__':
    main()
