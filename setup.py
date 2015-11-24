#!/usr/bin/env python3
import glob

from setuptools import setup, find_packages

import rsr.config

setup(
    name=rsr.config.name,
    version=rsr.config.version,
    description=rsr.config.description,
    author=rsr.config.author,
    author_email=rsr.config.author_email,
    url=rsr.config.url,
    packages=find_packages(),
    entry_points={
        'console_scripts': ['runsqlrun=rsr.cmd:main'],
    },
    data_files=[
        ('share/runsqlrun/icons',
         glob.glob('data/icons/*.svg')),
        ('share/icons/hicolor/scalable/apps',
         glob.glob('data/icons/*.svg')),
        ('share/runsqlrun/themes',
         glob.glob('data/themes/*.xml')),
        ('share/applications/',
         ['data/runsqlrun.desktop']),
    ]
)
