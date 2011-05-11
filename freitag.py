#!/usr/bin/env python
# encoding: utf-8
"""
freitag.py

Created by Giuseppe Capizzi on 2010-08-09.
Copyright (c) 2010 Giuseppe Capizzi. All rights reserved.
"""


import sys
import argparse # backported from 2.7
from string import replace, Template
from shutil import move
from os import makedirs, sep
from os.path import dirname, join
from re import sub, escape, search

from mutagen.mp3 import EasyMP3


DEFAULT_FORMAT = "%tracknumber - %artist - %title.mp3"


class FormatTemplate(Template):
    delimiter = '%'
    idpattern = '[a-z]+'


class FreiMP3(EasyMP3):
    def __getitem__(self, key):
        try:
            return super(EasyMP3, self).__getitem__(key)[0]
        except KeyError:
            return ''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['get', 'set', 'rename', 'extract'])
    parser.add_argument('files', nargs='+')
    parser.add_argument('--format', '-f', default=DEFAULT_FORMAT)
    # tag setters
    parser.add_argument('--album', '-b')
    parser.add_argument('--artist', '-a')
    parser.add_argument('--title', '-t')
    parser.add_argument('--discnumber', '-d')
    parser.add_argument('--tracknumber', '-n')
    parser.add_argument('--date', '-y')

    args = parser.parse_args()

    for filename in args.files:
        mp3 = FreiMP3(filename)

        if args.command == 'get':
            print get(mp3, args.format)
        elif args.command == 'set':
            set(mp3, args)
        elif args.command == 'rename':
            rename(mp3, args.format)
        elif args.command == 'extract':
            extract(mp3, args.format)


def get(mp3, format):
    return FormatTemplate(format).safe_substitute(mp3)


def set(mp3, args):
    # turn values from the command line into unicode strings,
    # remove unrelated and empty command line args
    tags = dict([(name, unicode(value)) for (name, value)
                 in args.__dict__.items()
                 if name not in ('command', 'files', 'format')
                 and value is not None])
    mp3.update(tags)
    mp3.save()


def rename(mp3, format):
    dest = get(mp3, format)

    # create missing directories
    try:
        makedirs(dirname(dest))
    except OSError:
        pass

    move(mp3.filename, dest)


def get_regex_for_tag(m):
    return '(?P<%(tagname)s>[^%(separator)s]*)' % {'tagname': m.group(1),
                                                   'separator': sep}


def extract(mp3, format):
    # we need a FormatTemplate instance to get delimiter and idpattern
    t = FormatTemplate('')
    # the regex pattern that matches tags in the format string
    # (delimiter must be escaped twice to be successfully substistuted in the
    # next step)
    tag_pattern = '%(del)s(%(pattern)s)' % {'del': escape(escape(t.delimiter)),
                                            'pattern': t.idpattern}

    # turn the format string into a regex and parse the filename
    regex = sub(tag_pattern, get_regex_for_tag, escape(format))
    values = search(regex, mp3.filename).groupdict()

    # convert all values to unicode
    values = dict([(name, unicode(value)) for (name,value) in values.items()])

    mp3.update(values)
    mp3.save()


if __name__ == '__main__':
    sys.exit(main())
