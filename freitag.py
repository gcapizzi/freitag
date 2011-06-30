#!/usr/bin/env python
# encoding: utf-8
#
# FreiTAG - A simple mp3 command line tool to tag and rename mp3s.
# Copyright (c) 2010-2011 Giuseppe Capizzi
# mailto: g.capizzi@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import argparse
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
    parser.add_argument('command', choices=['get', 'set', 'rename',
                                            'extract'])
    parser.add_argument('files', nargs='+')
    parser.add_argument('--format', '-f', default=DEFAULT_FORMAT,
                        help='The format used by "get", "rename" and '
                        + '"extract" commands. You can use the following '
                        + 'placeholders: %%album, %%artist, %%title, '
                        + '%%discnumber, %%tracknumber, %%date')
    # tag setters
    parser.add_argument('--album', '-b', help='The album name')
    parser.add_argument('--artist', '-a', help='The artist name')
    parser.add_argument('--title', '-t', help='The track title')
    parser.add_argument('--discnumber', '-d', help='The disc number')
    parser.add_argument('--tracknumber', '-n', help='The track number')
    parser.add_argument('--date', '-y', help='The track date (year)')

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
