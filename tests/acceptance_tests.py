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

from subprocess import Popen, PIPE
from shutil import copy
from os import remove, rename
from os.path import exists

from time import sleep

class AcceptanceTest(unittest.TestCase):

    TEST_MP3 = 'tests/test.mp3'
    TEMP_MP3 = 'tests/temp.mp3'

    LONG_FORMAT = '%tracknumber - %artist - %title (%date) - Disc %discnumber.mp3'
    FORMAT = '%tracknumber - %artist - %title.mp3'

    def setUp(self):
        copy(self.TEST_MP3, self.TEMP_MP3)

    def tearDown(self):
        if exists(self.TEMP_MP3):
            remove(self.TEMP_MP3)

    def run_freitag(self, *params):
        cmd = ['bin/freitag'] + list(params)
        return Popen(cmd, stdout=PIPE).communicate()[0]

    def test_get(self):
        output = self.run_freitag('get', self.TEMP_MP3)
        self.assertEquals('01 - Bob Marley - One Love.mp3\n', output)

    def test_get_with_custom_format(self):
        output = self.run_freitag('get', self.TEMP_MP3,
                                  '--format=%s' % self.LONG_FORMAT)
        self.assertEquals('01 - Bob Marley - One Love (1977) - Disc 1.mp3\n',
                          output)

    def test_set(self):
        self.run_freitag('set', '--artist=Dennis Brown',
                         '--title=Revolution', '--tracknumber=5',
                         self.TEMP_MP3)
        output = self.run_freitag('get', self.TEMP_MP3)
        self.assertEquals('05 - Dennis Brown - Revolution.mp3\n', output)

    def test_rename(self):
        expected_filename = 'tests/01 - Bob Marley - One Love.mp3'
        self.assertTrue(exists(self.TEMP_MP3))
        self.assertFalse(exists(expected_filename))
        self.run_freitag('rename', self.TEMP_MP3,
                         '--format=tests/%s' % self.FORMAT)
        self.assertTrue(exists(expected_filename))
        self.assertFalse(exists(self.TEMP_MP3))
        remove(expected_filename)

    def test_extract(self):
        filename = 'tests/12 - Burial - Peter Tosh.mp3'
        rename(self.TEMP_MP3, filename)
        self.run_freitag('extract', filename,
                         '--format=%tracknumber - %title - %artist.mp3')
        output = self.run_freitag('get', filename)
        self.assertEquals('12 - Peter Tosh - Burial.mp3\n', output)
        remove(filename)

    def test_humanize(self):
        self.run_freitag('set', '--title=One_love', '--artist=bob marley',
                         '--album=EXODUS', self.TEMP_MP3)
        self.run_freitag('humanize', self.TEMP_MP3)
        output = self.run_freitag('get', self.TEMP_MP3)
        self.assertEquals('01 - Bob Marley - One Love.mp3\n', output)


if __name__ == '__main__':
    unittest.main()
