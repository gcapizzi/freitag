#!/usr/bin/env python
# encoding: utf-8
#
# FreiTAG - A simple command line tool to tag and rename mp3s.
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


import argparse
import locale
from sys import exit
from string import Template, capwords
from os import makedirs, sep
from os.path import dirname, exists
from shutil import move
from re import sub, search

from mutagen.mp3 import EasyMP3

locale.setlocale(locale.LC_ALL, '')
ENCODING = locale.getlocale()[1]

class FormatTemplate(Template):

    """A custom Template subclass used for tag extraction."""

    delimiter = '%'
    idpattern = '[a-z]+'


class FreiSong:

    """The main FreiTag class, representing a song."""

    DEFAULT_FORMAT = "%tracknumber - %artist - %title.mp3"
    TAGS = {
        'album':       {'abbr': 'b', 'help': 'The album name'},
        'artist':      {'abbr': 'a', 'help': 'The artist name'},
        'title':       {'abbr': 't', 'help': 'The track title'},
        'discnumber':  {'abbr': 'd', 'help': 'The disc number'},
        'tracknumber': {'abbr': 'n', 'help': 'The track number'},
        'date':        {'abbr': 'y', 'help': 'The track date (year)'}
    }

    def __init__(self, mp3):
        self.mp3 = mp3
        self.prev_filename = mp3.filename
        self.filename = mp3.filename

    def __getitem__(self, key):
        value = ''

        try:
            value = self.mp3[key]
            # mutagen tags can be lists
            if isinstance(value, list):
                value = value[0]

            # remove the slash and everything after it in track number
            # and zero-pad it
            if key == 'tracknumber':
                value = value.split('/')[0].rjust(2, '0')
        except KeyError:
            pass

        return value

    def __setitem__(self, key, value):
        self.mp3[key] = value

    def update(self, tags):
        """Update song with tags."""
        # ignore unsupported tags
        tags = dict((name, value) for name, value in tags.items()
                if name in self.TAGS and value is not None)
        # convert everything to unicode
        tags = dict((name, unicode(value, ENCODING)) for (name, value) in tags.items())
        self.mp3.update(tags)

    def save(self):
        """Save the song."""
        self.mp3.save()

        # rename if necessary
        if self.filename != self.prev_filename and not exists(self.filename):
            move(self.prev_filename, self.filename)
            self.prev_filename = self.filename

        # update mp3 filename accordingly
        self.mp3.filename = self.filename

    def format(self, format):
        """Return a string representation of the song according to the specified
        format.

        """
        return FormatTemplate(format).safe_substitute(self).strip()

    def rename(self, format):
        """Rename song according to the specified format."""
        self.filename = self.format(format)

    def extract(self, format):
        """Extracts values from a string according to the specified format."""
        # the regex pattern that matches tags in the format string
        tag_pattern = '{delimiter}({pattern})'.format(
                delimiter=FormatTemplate.delimiter,
                pattern=FormatTemplate.idpattern)

        def _get_regex_for_tag(m):
            """Take a match object and return a regex with a properly named
            group.

            """
            tag_name = m.group(1)
            tag_regex = '[^%s]*' % sep

            # non-greedy regex for tracknumber tag
            if tag_name == 'tracknumber':
                tag_regex += '?'

            return '(?P<{tag_name}>{tag_regex})'.format(tag_name=tag_name,
                                                        tag_regex=tag_regex)

        # turn the format string into a regex and parse the filename
        regex = sub(tag_pattern, _get_regex_for_tag, format)

        self.update(search(regex, self.filename).groupdict())

    def humanize(self):
        """Humanize album, title and artist tags from tags dictionary."""
        tags_to_humanize = ['album', 'artist', 'title']

        for tag in tags_to_humanize:
            if tag in self.mp3:
                self[tag] = capwords(self[tag].replace('_', ' '))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['get', 'set', 'rename',
                                            'extract', 'humanize'])
    parser.add_argument('files', nargs='+')
    parser.add_argument('--format', '-f', default=FreiSong.DEFAULT_FORMAT,
                        help='The format used by "get", "rename" and '
                        + '"extract" commands. You can use the following '
                        + 'placeholders: '
                        + ', '.join(['%%{0}'.format(t)
                                     for t in FreiSong.TAGS]))
    parser.add_argument('--humanize', action="store_true", default=False,
                        help='When extracting, convert all fields from '
                        + 'lowecase_with_underscores format to Capitalized '
                        + 'With Spaces format')

    # tag setters
    for tag, props in FreiSong.TAGS.iteritems():
        long_opt = '--%s' % tag
        short_opt = '-%s' % props['abbr']
        parser.add_argument(long_opt, short_opt, help=props['help'])

    args = parser.parse_args()

    songs = [FreiSong(EasyMP3(file)) for file in args.files]

    # If not calling the 'get' command, try to import clint.
    # If clint is imported successfully, use it to print a progress bar.
    if args.command != 'get':
        try:
            from clint.textui import progress
        except ImportError:
            pass
        else:
            songs = progress.bar(songs)

    if args.command == 'get':
        get(songs, args.format)
    elif args.command == 'set':
        set(songs, args)
    elif args.command == 'rename':
        rename(songs, args.format)
    elif args.command == 'extract':
        extract(songs, args.format, args.humanize)
    elif args.command == 'humanize':
        humanize(songs)


def get(songs, format):
    """Print the songs informations according to the specified format."""
    for song in songs:
        print song.format(format)


def set(songs, args):
    """Tag songs using arguments from argparse."""
    for song in songs:
        song.update(args.__dict__)
        song.save()


def rename(songs, format):
    """Rename songs according to format."""
    for song in songs:
        song.rename(format)
        song.save()


def extract(songs, format, humanize=False):
    """Tag songs extracting tag values from its filename according to format.

    If humanize is True, humanize tags before tagging.

    """
    for song in songs:
        song.extract(format)

        # humanize
        if humanize:
            song.humanize()

        song.save()


def humanize(songs):
    """Humanize album, artist and title tags in songs."""
    for song in songs:
        song.humanize()
        song.save()


if __name__ == '__main__':
    exit(main())
