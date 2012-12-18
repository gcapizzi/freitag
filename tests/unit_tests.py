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

from freitag import FreiSong

from mutagen.mp3 import EasyMP3

from exam.mock import Mock

class TestFreiSong(unittest.TestCase):

    def setUp(self):
        _tags = {'tracknumber': ['1/2'], 'title': ['One Love'],
                 'artist': ['Bob Marley'], 'album': ['Exodus']}
        def getitem(name):
            return _tags[name]
        def setitem(name, val):
            _tags[name] = val
        def contains(key):
            return key in _tags

        self.mp3 = Mock()
        self.mp3.__getitem__  = Mock(side_effect=getitem)
        self.mp3.__setitem__  = Mock(side_effect=setitem)
        self.mp3.__contains__ = Mock(side_effect=contains)
        self.mp3.filename = 'Bob Marley - One Love.mp3'

        self.song = FreiSong(self.mp3)

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

    def test_update(self):
        self.song.update({'artist': 'Dennis Brown', 'title': 'Here I Come',
                          'foo': 'bar'})

        self.mp3.update.assert_called_with({'artist': 'Dennis Brown',
                                            'title': 'Here I Come'})

    def test_save(self):
        self.song.save()

        self.mp3.save.assert_called_with()

    def test_format(self):
        format = '%artist - %title'

        self.assertEqual('Bob Marley - One Love', self.song.format(format))

    def test_rename(self):
        format = '%title - %artist.mp3'
        self.song.rename(format)

        self.assertEqual('One Love - Bob Marley.mp3', self.song.filename)

    def test_extract(self):
        format = '%artist - %title.mp3'
        self.song.filename = 'Dennis Brown - Here I Come.mp3'
        self.song.extract(format)

        self.mp3.update.assert_called_with({'artist': 'Dennis Brown',
                                            'title':  'Here I Come'})

    def test_humanize(self):
        self.song['title']  = 'One_love'
        self.song['artist'] = 'bob marley'
        self.song['album']  = 'EXODUS'
        self.song.humanize()

        self.assertEqual('One Love',   self.song['title'])
        self.assertEqual('Bob Marley', self.song['artist'])
        self.assertEqual('Exodus',     self.song['album'])


if __name__ == '__main__':
    unittest.main()
