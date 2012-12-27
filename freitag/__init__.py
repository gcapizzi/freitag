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


from string import Template, capwords
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


class FileSystem:
    def rename(self, old_name, new_name):
        move(old_name, new_name)


class FreiSong:

    """The main FreiTag class, representing a song."""

    def __init__(self, mp3, filesystem=FileSystem(),
                 template=FreiTemplate(DEFAULT_FORMAT)):
        self.mp3 = mp3
        self.prev_filename = mp3.filename
        self.filename = mp3.filename
        self.filesystem = filesystem
        self.template = template

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

    def format(self):
        """Return a string representation of the song according to the
        specified format.

        """
        return self.template.safe_substitute(self).strip()

    def rename(self):
        """Rename song according to the specified format."""
        self.filename = self.format()

    def extract(self):
        """Extracts values from a string according to the specified format."""
        tags = self._extract_tags(self.filename, self.template.template)
        self.update(tags)

    def _extract_tags(self, filename, format):
        regex = self._format_to_regex(format)
        return search(regex, filename).groupdict()

    def _format_to_regex(self, format):
        # the regex pattern that matches tags in the format string
        format_opts = {'delimiter': self.template.delimiter,
                       'pattern': self.template.idpattern}
        tag_pattern = '{delimiter}({pattern})'.format(**format_opts)

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

        return sub(tag_pattern, _get_regex_for_tag, format)

    def humanize(self):
        """Humanize album, title and artist tags from tags dictionary."""
        tags_to_humanize = ['album', 'artist', 'title']

        for tag in tags_to_humanize:
            if tag in self.mp3:
                self[tag] = self._humanize_tag(self[tag])

    def _humanize_tag(self, string):
        return capwords(string.replace('_', ' '))
