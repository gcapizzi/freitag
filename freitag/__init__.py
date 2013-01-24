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


from string import Template
from os import sep
from os.path import exists
from shutil import move
from re import sub, search

from mutagen.mp3 import EasyMP3


DEFAULT_FORMAT = "%tracknumber - %artist - %title.mp3"
TAGS = {
    'album':       {'abbr': 'b', 'help': 'The album name'},
    'artist':      {'abbr': 'a', 'help': 'The artist name'},
    'title':       {'abbr': 't', 'help': 'The track title'},
    'discnumber':  {'abbr': 'd', 'help': 'The disc number'},
    'tracknumber': {'abbr': 'n', 'help': 'The track number'},
    'date':        {'abbr': 'y', 'help': 'The track date (year)'}
}


class FreiTemplate(Template):

    """A custom Template subclass used for tag extraction."""

    delimiter = '%'
    idpattern = '[a-z]+'

    def format(self, values):
        return self.safe_substitute(values).strip()

    def extract(self, string):
        regex = self._template_to_regex(self.template)
        return search(regex, string).groupdict()

    def _tag_to_regex(self, tag):
        tag_regex = '[^%s]*' % sep

        # non-greedy regex for tracknumber tag
        # TODO this is a hack!
        if tag == 'tracknumber':
            tag_regex += '?'

        return '(?P<{0}>{1})'.format(tag, tag_regex)

    def _template_to_regex(self, template):
        # the regex pattern that matches tags in the template string
        tag_pattern = '{0}({1})'.format(self.delimiter, self.idpattern)
        tag_to_regex = lambda m: self._tag_to_regex(m.group(1))
        return sub(tag_pattern, tag_to_regex, template)


class FileSystem:

    def rename(self, old_name, new_name):
        move(old_name, new_name)


class FreiSong:

    """The main FreiTag class, representing a song."""

    def __init__(self, mp3, filesystem=FileSystem()):
        self.mp3 = mp3
        self.prev_filename = mp3.filename
        self.filename = mp3.filename
        self.filesystem = filesystem

    def __getitem__(self, key):
        value = ''

        if key in self.mp3:
            value = self._first(self.mp3[key])

            # remove the slash and everything after it in track number
            # and zero-pad it
            if key == 'tracknumber':
                value = self._fix_tracknumber(value)

        return value

    def _first(self, single_or_list):
        if isinstance(single_or_list, list):
            return single_or_list[0]
        return single_or_list

    def _fix_tracknumber(self, tracknumber):
        return tracknumber.split('/')[0].rjust(2, '0')

    def __contains__(self, tag):
        return tag in self.mp3

    def __setitem__(self, key, value):
        if key in self.mp3:
            self.mp3[key] = value

    def update(self, tags):
        """Update song with tags."""
        tags = self._filter_tags(tags)
        tags = self._unicode_tags(tags)
        self.mp3.update(tags)

    def _filter_tags(self, tags):
        return dict((name, value) for name, value in tags.items()
                    if name in TAGS and value is not None)

    def _unicode_tags(self, tags):
        return dict((name, unicode(value)) for (name, value) in tags.items())

    def save(self):
        """Save the song."""
        self.mp3.save()
        self._rename()

    def _rename(self):
        if self.filename != self.prev_filename and not exists(self.filename):
            self.filesystem.rename(self.prev_filename, self.filename)
            self.prev_filename = self.filename

        self.mp3.filename = self.filename
