#! /usr/bin/env python

from setuptools import setup

setup(name='freitag',
    version='0.1',
    description='Simple command line tool to tag and rename mp3s',
    keywords=['mp3', 'tag'],
    author='Giuseppe Capizzi',
    author_email='g.capizzi@gmail.com',
    url='https://github.com/gcapizzi/freitag',
    license='GPL3',
    packages=[],
    py_modules=['freitag'],
    install_requires=['mutagen', 'clint'],
    entry_points={'console_scripts': ['freitag = freitag:main']}
)

