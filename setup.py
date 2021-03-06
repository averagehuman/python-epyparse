#!/usr/bin/env python

from distutils.core import setup

import sys
import os
srcdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, srcdir)
__version__ = '0.2.3'
readme = open("README").read()
changes = open("docs/changes.rst").read()
long_description = readme + "\n\n" + changes
requires = [
    'epydoc',
    'python-modargs',
]

setup(
    name="epyparse",
    version=__version__,
    author="Gerard Flanagan",
    author_email="grflanagan@gmail.com",
    description="Generate API info for Python Packages via Epydoc",
    long_description=long_description,
    download_url="http://pypi.python.org/packages/source/e/epyparse/epyparse-%s.tar.gz" % __version__,
    py_modules=['epyparse'],
    scripts = [
        os.path.join(srcdir, 'bin', 'epyparse'),
    ],
    install_requires=requires,
)

