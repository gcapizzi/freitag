#!/usr/bin/env python
# encoding: utf-8
#
# FreiTAG - A simple song command line tool to tag and rename songs.
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


import unittest

from nose.tools import *
from exam.mock import Mock, call

from mutagen.mp3 import EasyMP3

from freitag import FreiSong, FreiTemplate, DEFAULT_FORMAT
from freitag.operations import (RenameOperation, ExtractOperation,
                                HumanizeOperation)


class TestFreiSong(unittest.TestCase):

    def setUp(self):
        _tags = {'tracknumber': ['1/2'], 'title': ['One Love'],
                 'artist': ['Bob Marley'], 'album': ['Exodus']}

        self._song_name = 'Bob Marley - One Love'
        self._filename = self._song_name + '.mp3'
        self._new_filename = 'Dennis Brown - Here I Come.mp3'

        def getitem(name):
            return _tags[name]

        def contains(key):
            return key in _tags

        self.mp3 = Mock()
        self.mp3.__getitem__ = Mock(side_effect=getitem)
        self.mp3.__setitem__ = Mock()
        self.mp3.__contains__ = Mock(side_effect=contains)
        self.mp3.filename = self._filename

        self.filesystem = Mock()

        self.template = Mock()
        self.template.template = DEFAULT_FORMAT
        self.template.idpattern = FreiTemplate.idpattern
        self.template.delimiter = FreiTemplate.delimiter
        self.template.safe_substitute.return_value = self._song_name + '   '

        self.song = FreiSong(self.mp3, filesystem=self.filesystem)

    def test_getitem(self):
        self.assertEqual('Bob Marley', self.song['artist'])
        self.mp3.__getitem__.assert_called_with('artist')

        self.assertEqual('01', self.song['tracknumber'])
        self.mp3.__getitem__.assert_called_with('tracknumber')

        self.assertEqual('', self.song['foo'])
        self.mp3.__getitem__.assert_not_called_with('foo')

    def test_setitem(self):
        self.song['title'] = 'Here I Come'
        self.mp3.__setitem__.assert_called_with('title', 'Here I Come')

        self.song['foo'] = 'bar'
        self.mp3.__setitem__.assert_not_called_with('foo', 'bar')

    def test_contains(self):
        self.assertTrue('artist' in self.song)
        self.mp3.__contains__.assert_called_with('artist')

    def test_update(self):
        self.song.update({'artist': 'Dennis Brown', 'title': 'Here I Come',
                          'foo': 'bar'})

        self.mp3.update.assert_called_with({'artist': 'Dennis Brown',
                                            'title': 'Here I Come'})

    def test_save(self):
        self.song.filename = self._new_filename
        self.song.save()

        self.mp3.save.assert_called_with()
        self.assertEquals(self._new_filename, self.mp3.filename)
        self.filesystem.rename.assert_called_with(self._filename,
                                                  self._new_filename)

        self.song.save()
        self.filesystem.rename.assert_not_called_with(self._new_filename,
                                                      self._new_filename)


class FreiTemplateTest(unittest.TestCase):

    def test_format(self):
        tags = {'artist': 'Bob Marley', 'title': 'One Love'}
        template = FreiTemplate('   %artist - %title   ')
        self.assertEquals('Bob Marley - One Love', template.format(tags))


class RenameOperationTest(unittest.TestCase):

    def setUp(self):
        self.song = Mock()
        self.template = Mock()
        self.filename = ' a filename '
        self.template.safe_substitute.return_value = self.filename
        self.rename_operation = RenameOperation(self.template)

    def test_apply(self):
        self.rename_operation.apply(self.song)
        self.template.safe_substitute.assert_called_with(self.song)
        expected_filename = 'a filename'
        self.assertEquals(expected_filename, self.song.filename)


class ExtractOperationTest(unittest.TestCase):

    def setUp(self):
        self.song = Mock()
        self.song.filename = '01 - Dennis Brown - Here I Come.mp3'
        self.extract_operation = ExtractOperation()

    def test_apply(self):
        self.extract_operation.apply(self.song)

        self.song.update.assert_called_with({'tracknumber': '01',
                                            'artist': 'Dennis Brown',
                                            'title':  'Here I Come'})


class HumanizeOperationTest(unittest.TestCase):

    def setUp(self):
        tags = {'title': 'One_love', 'artist': 'bob marley', 'album': 'EXODUS'}
        self.song = Mock()
        self.song.__getitem__ = Mock(side_effect=lambda tag: tags[tag])
        self.song.__setitem__ = Mock()
        self.song.__contains__ = Mock()

        self.humanize_operation = HumanizeOperation()

    def test_apply(self):
        self.humanize_operation.apply(self.song)

        expected_setitem_calls = [call('title', 'One Love'),
                                  call('artist', 'Bob Marley'),
                                  call('album', 'Exodus')]
        actual_setitem_calls = self.song.__setitem__.call_args_list

        expected_contains_calls = [call('title'), call('artist'),
                                   call('album')]
        actual_contains_calls = self.song.__contains__.call_args_list

        for expected_call in expected_setitem_calls:
            self.assertTrue(expected_call in actual_setitem_calls)

        for expected_call in expected_contains_calls:
            self.assertTrue(expected_call in actual_contains_calls)


if __name__ == '__main__':
    unittest.main()
