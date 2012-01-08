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


import argparse
from sys import exit
from string import replace, Template, capwords
from shutil import move
from os import makedirs, sep
from os.path import dirname, join, exists
from re import sub, escape, search

from mutagen.mp3 import EasyMP3

TAG_DELIMITER = '%'
TAG_IDPATTERN = '[a-z]+'
DEFAULT_FORMAT = "%tracknumber - %artist - %title.mp3"
TAGS = {
    'album':       {'abbr': 'b', 'help': 'The album name'},
    'artist':      {'abbr': 'a', 'help': 'The artist name'},
    'title':       {'abbr': 't', 'help': 'The track title'},
    'discnumber':  {'abbr': 'd', 'help': 'The disc number'},
    'tracknumber': {'abbr': 'n', 'help': 'The track number'},
    'date':        {'abbr': 'y', 'help': 'The track date (year)'}
 }


class FormatTemplate(Template):
    """Custom `string.Template` subclass used in `_format`."""
    delimiter = TAG_DELIMITER
    idpattern = TAG_IDPATTERN


class FreiMP3(EasyMP3):
    """Custom, simplified `mutagen.mp3.EasyMP3` subclass."""
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
                        + ', '.join(['%%{0}'.format(t) for t in TAGS]))
    parser.add_argument('--humanize', action="store_true", default=False,
                        help='When extracting, convert all fields from '
                        + 'lowecase_with_underscores format to Capitalized '
                        + 'With Spaces format')

    # tag setters
    for tag, props in TAGS.iteritems():
        long_opt = '--%s' % tag
        short_opt = '-%s' % props['abbr']
        parser.add_argument(long_opt, short_opt, help=props['help'])

    args = parser.parse_args()

    mp3s = _mp3s(args.files)

    if args.command == 'get':
        get(mp3s, args.format)
    elif args.command == 'set':
        set(mp3s, args)
    elif args.command == 'rename':
        rename(mp3s, args.format)
    elif args.command == 'extract':
        extract(mp3s, args.format, args.humanize)
    elif args.command == 'humanize':
        humanize(mp3s)


def _mp3s(files):
    """Return a list of `FreiMP3` instances from a list of files."""
    return [FreiMP3(file) for file in files]


def _format(string, dictionary):
    """Substitute tags in the %tag form with values from dictionary.

    >>> _format("%artist - %title", {'artist': 'Bob Marley', \
                                     'title':  'One Love'})
    'Bob Marley - One Love'
    """
    return FormatTemplate(string).safe_substitute(dictionary)


def get(mp3s, format):
    """Print the songs informations according to the specified format."""
    for mp3 in mp3s:
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
    """Filter out every entry in dictionary that is not a tag or is None.

    >>> unfiltered = {'artist': 'Bob Marley', 'title': 'One Love', 'foo': 'bar'}
    >>> filtered = _filter_tags(unfiltered)
    >>> expected = {'artist': 'Bob Marley', 'title': 'One Love'}
    >>> filtered == expected
    True
    """
    return dict((name, value) for name, value in dictionary.items()
                if name in TAGS and value is not None)


def set(mp3s, args):
    """Tag mp3s using arguments from argparse."""
    for mp3 in mp3s:
        _save(mp3, _filter_tags(args.__dict__))


def rename(mp3s, format):
    """Rename mp3s according to format."""
    for mp3 in mp3s:
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

    This function is made to be used as replacement function in a `re.sub` call.
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


def extract(mp3s, format, humanize=False):
    """Tag mp3s extracting tag values from its filename according to format.

    If humanize is True, humanize tags before tagging.
    """
    for mp3 in mp3s:
        tags = _extract(mp3.filename, format)

        # humanize
        if humanize:
            tags = _humanize_tags(tags)

        _save(mp3, tags)


def humanize(mp3s):
    """Humanize album, artist and title tags in mp3s."""
    for mp3 in mp3s:
        _save(mp3, _humanize_tags(tags))


if __name__ == '__main__':
    exit(main())
