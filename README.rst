=======
FreiTag
=======

FreiTag is a command line tool to tag and rename your MP3s. It can:

* print MP3s tags,
* tag MP3s according to values you specify,
* tag MP3s extracting tag values from the file name,
* rename MP3s using tags.

Printing tags
=============

FreiTag can print tags according to a format. Just type:

.. code-block:: shell

    $ freitag get song.mp3
    01 - Artist - Title.mp3

To specify your own format, use the format parameter:

.. code-block:: shell

    $ freitag get song.mp3 --format="*** %artist ***"
    *** Artist ***

The format string can contain the following placeholders:

* %artist
* %title
* %album
* %tracknumber
* %date
* %discnumber
