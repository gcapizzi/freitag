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


from mutagen.mp3 import EasyMP3

from freitag import FreiSong, FreiTemplate
from freitag.operations import (SetOperation, RenameOperation,
                                ExtractOperation, HumanizeOperation)


class Command:

    def get_songs(self, files):
        return [FreiSong(EasyMP3(file)) for file in files]

    def run(self, args):
        raise NotImplementError


class GetCommand(Command):

    def run(self, args):
        songs = self.get_songs(args.files)
        template = FreiTemplate(args.format)
        for song in songs:
            print template.format(song)


class OperationCommand(Command):

    def __init__(self, operation):
        self.operation = operation

    def progress_bar(self, songs):
        try:
            from clint.textui import progress
        except ImportError:
            return songs
        else:
            return progress.bar(songs)

    def get_songs_and_progress_bar(self, files):
        return self.progress_bar(self.get_songs(files))

    def apply_operation_and_save(self, operation, files):
        songs = self.get_songs_and_progress_bar(files)
        for song in songs:
            operation.apply(song)
            song.save()

    def run(self, args):
        self.apply_operation_and_save(self.operation, args.files)


class CommandFactory:

    COMMANDS = ['get', 'set', 'rename', 'extract', 'humanize']

    def from_args(self, args):
        name = args.command

        if name == 'get':
            return GetCommand()
        elif name == 'set':
            return OperationCommand(SetOperation(args.__dict__))
        elif name == 'rename':
            template = FreiTemplate(args.format)
            return OperationCommand(RenameOperation(template))
        elif name == 'extract':
            template = FreiTemplate(args.format)
            return OperationCommand(ExtractOperation(template))
        elif name == 'humanize':
            return OperationCommand(HumanizeOperation())
