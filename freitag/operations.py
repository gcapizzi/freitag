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


from re import sub
from string import capwords

from freitag import FreiTemplate, DEFAULT_FORMAT


class Operation:

    def apply(self, song):
        raise NotImplementError


class SetOperation(Operation):

    def __init__(self, tags):
        self.tags = tags

    def apply(self, song):
        song.update(self.tags)


class RenameOperation(Operation):

    def __init__(self, template=FreiTemplate(DEFAULT_FORMAT)):
        self.template = template

    def _format(self, song):
        return self.template.safe_substitute(song).strip()

    def apply(self, song):
        """Rename song according to the specified format."""
        song.filename = self._format(song)


class ExtractOperation(Operation):

    def __init__(self, template=FreiTemplate(DEFAULT_FORMAT)):
        self.template = template

    def apply(self, song):
        tags = self.template.extract(song.filename)
        song.update(tags)


class HumanizeOperation(Operation):

    def apply(self, song):
        """Humanize album, title and artist tags from tags dictionary."""
        tags_to_humanize = ['album', 'artist', 'title']

        for tag in tags_to_humanize:
            if tag in song:
                song[tag] = self._humanize_tag(song[tag])

    def _humanize_tag(self, string):
        return capwords(string.replace('_', ' '))
