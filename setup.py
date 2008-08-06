#!/usr/bin/env python
# -*- coding:utf-8 -*-

""" setup file for static render """

import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages

setup(
    name = 'StaticRender',
    version = '0.1',
    author = 'Florian Heinle',
    description = '''SR means to provide easy methods for rendering plaintext
    files with human readable formatting into static html files, for situations
    when no complete/dynamic CMS is necessary.''',
    packages = find_packages(),
    entry_points = {
        'console_scripts': ['sr = sr.sr:main',]
    },
    platforms = 'any',
    include_package_data = True,
    classifiers = [
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Intended Audience :: End Users/Desktop',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
    ],
    install_requires = 'markdown',
    extras_require = {
        'Syntax Highlighting':['pygments'],
    }
)
