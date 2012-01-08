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
from string import replace, Template, capwords
from shutil import move
from os import makedirs, sep
from os.path import dirname, join, exists
from re import sub, escape, search

from mutagen.mp3 import EasyMP3

TAG_DELIMITER = '%'
TAG_IDPATTERN = '[a-z]+'
DEFAULT_FORMAT = "%tracknumber - %artist - %title.mp3"
TAGS = [
    {'name': 'album',       'abbr': 'b', 'help': 'The album name'},
    {'name': 'artist',      'abbr': 'a', 'help': 'The artist name'},
    {'name': 'title',       'abbr': 't', 'help': 'The track title'},
    {'name': 'discnumber',  'abbr': 'd', 'help': 'The disc number'},
    {'name': 'tracknumber', 'abbr': 'n', 'help': 'The track number'},
    {'name': 'date',        'abbr': 'y', 'help': 'The track date (year)'}
]


class FormatTemplate(Template):
    delimiter = TAG_DELIMITER
    idpattern = TAG_IDPATTERN


class FreiMP3(EasyMP3):
    def __getitem__(self, key):
        value = ''

        try:
            value = super(EasyMP3, self).__getitem__(key)[0]

            # remove the slash and everything after it in track number
            # and zero-pad it
            if key == 'tracknumber':
                value = value.split('/')[0].rjust(2, '0')
        except KeyError:
            pass

        return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['get', 'set', 'rename',
                                            'extract', 'humanize'])
    parser.add_argument('files', nargs='+')
    parser.add_argument('--format', '-f', default=DEFAULT_FORMAT,
                        help='The format used by "get", "rename" and '
                        + '"extract" commands. You can use the following '
                        + 'placeholders: '
                        + ', '.join(['%%{0}'.format(t['name']) for t in TAGS]))
    parser.add_argument('--humanize', action="store_true", default=False,
                        help='When extracting, convert all fields from '
                        + 'lowecase_with_underscores format to Capitalized '
                        + 'With Spaces format')

    # tag setters
    for tag in TAGS:
        long_opt = '--%s' % tag['name']
        short_opt = '-%s' % tag['abbr']
        parser.add_argument(long_opt, short_opt, help=tag['help'])

    args = parser.parse_args()

    for filename in args.files:
        mp3 = FreiMP3(filename)

        if args.command == 'get':
            get(mp3, args.format)
        elif args.command == 'set':
            set(mp3, args)
        elif args.command == 'rename':
            rename(mp3, args.format)
        elif args.command == 'extract':
            extract(mp3, args.format, args.humanize)
        elif args.command == 'humanize':
            humanize(mp3)


def _format(string, dictionary):
    """Substitute tags in the %tag form with values from dictionary.

    >>> _format("%artist - %title", {'artist': 'Bob Marley', \
                                     'title':  'One Love'})
    'Bob Marley - One Love'
    """
    return FormatTemplate(string).safe_substitute(dictionary)


def get(mp3, format):
    """Print the song informations according to the specified format."""
    print _format(format, mp3).strip()


def _unicode(dictionary):
    """Convert all values in dictionary to unicode strings.

    >>> _unicode({'artist': 'Bob Marley', 'title': 'One Love'})
    {'artist': u'Bob Marley', 'title': u'One Love'}
    """
    return dict((name, unicode(value)) for (name, value) in dictionary.items())


def _save(mp3, tags):
    """Update mp3 with tags and save it."""
    mp3.update(_unicode(tags))
    mp3.save()


def _filter_tags(dictionary):
    """Filter out every entry in dictionary that is not an mp3 tag or is None.

    >>> filtered = _filter_tags({'artist': 'Bob Marley', 'title': 'One Love', \
                                 'foo': 'bar'})
    >>> expected = {'artist': 'Bob Marley', 'title': 'One Love'}
    >>> filtered == expected
    True
    """
    tag_names = [tag['name'] for tag in TAGS]
    return dict((name, value) for name, value in dictionary.items()
                if name in tag_names and value is not None)


def set(mp3, args):
    _save(mp3, _filter_tags(args.__dict__))


def rename(mp3, format):
    dest = _format(format, mp3)

    # create missing directories
    try:
        makedirs(dirname(dest))
    except OSError:
        pass

    if (exists(dest)):
        print "%s already exists! Skipping..." % dest
        return
    else:
        move(mp3.filename, dest)


def _get_regex_for_tag(m):
    """Take a match object and return a regex with a properly named group.

    This function is made to be used as replacement function in a re.sub() call.
    """
    tag_name = m.group(1)
    tag_regex = '[^%s]*' % sep

    # non-greedy regex for tracknumber tag
    if tag_name == 'tracknumber':
        tag_regex += '?'

    return '(?P<{tag_name}>{tag_regex})'.format(tag_name=tag_name,
                                                tag_regex=tag_regex)


def _humanize(string):
    """Convert string from lowecase_with_underscores to Capitalized With Spaces.

    >>> _humanize('bob_marley_-_one_love')
    'Bob Marley - One Love'
    """
    return capwords(string.replace('_', ' '))


def _humanize_tags(tags):
    """Humanize album, title and artist tags from tags dictionary.

    >>> humanized = _humanize_tags({'artist': 'bob marley', \
                                    'title':  'One_love', \
                                    'album':  'Exodus'})
    >>> expected = {'album': 'Exodus', 'title': 'One Love', \
                    'artist': 'Bob Marley'}
    >>> humanized == expected
    True
    """
    tags_to_humanize = ['album', 'artist', 'title']

    for tag in tags_to_humanize:
        if tags.has_key(tag):
            tags[tag] = _humanize(tags[tag])

    return tags


def _extract(string, format):
    """Extracts values from a string according to the specified format.

    >>> extracted = _extract('Bob Marley - One Love', '%artist - %title')
    >>> expected = {'artist': 'Bob Marley', 'title': 'One Love'}
    >>> extracted == expected
    True
    """
    # the regex pattern that matches tags in the format string
    tag_pattern = '{delimiter}({pattern})'.format(delimiter=TAG_DELIMITER,
                                                  pattern=TAG_IDPATTERN)

    # turn the format string into a regex and parse the filename
    regex = sub(tag_pattern, _get_regex_for_tag, format)

    return search(regex, string).groupdict()


def extract(mp3, format, humanize=False):
    tags = _extract(mp3.filename, format)

    # humanize
    if humanize:
        tags = _humanize_tags(tags)

    _save(mp3, tags)


def humanize(mp3):
    _save(mp3, _humanize_tags(tags))


if __name__ == '__main__':
    sys.exit(main())
