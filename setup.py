from distutils.core import setup

setup(
    name='freitag',
    version='0.1.0',
    author='G. Capizzi',
    author_email='g.capizzi@gmail.com',
    packages=['freitag'],
    scripts=['bin/freitag'],
    url='http://pypi.python.org/pypi/freitag/',
    license='COPYING.txt',
    description='A command-line tool for MP3 tagging and renaming.',
    long_description=open('README.rst').read(),
    install_requires=[
        "argparse >= 1.2.1",
        "mutagen >= 1.2.0",
    ],
)
