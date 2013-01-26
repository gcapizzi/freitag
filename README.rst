=======
FreiTag
=======

FreiTag is a command line tool to tag and rename your MP3s. It can:

* print MP3s tags,
* tag MP3s according to values you specify,
* tag MP3s extracting tag values from the file name,
* rename MP3s using tags,
* humanize tags.

Installation
============

Just use :code:`pip` or :code:`easy_install`:

.. code-block:: shell

    $ pip install freitag

Usage
=====

Printing tags
-------------

FreiTag can print tags according to a format you specify. Just type:

.. code-block:: shell

    $ freitag get song.mp3 --format="%artist - %title.mp3"
    Bob Marley - One Love.mp3

The format string can contain the following placeholders:

* :code:`%artist`
* :code:`%title`
* :code:`%album`
* :code:`%tracknumber`
* :code:`%date`
* :code:`%discnumber`

Setting tags
------------

To set specific values for the song tags, use the following parameters:

* :code:`--artist`
* :code:`--title`
* :code:`--album`
* :code:`--tracknumber`
* :code:`--date`
* :code:`--discnumber`

For example:

.. code-block:: shell

    $ freitag set song.mp3 --title="Exodus"
    $ freitag get song.mp3 --format="%artist - %title"
    Bob Marley - Exodus

Extracting tags
---------------

If your file is well-named but its tags are wrong and/or missing, you can
extract tags from the file name itself. Of course you'll have to specify the
format used by the name of the file.

.. code-block:: shell

    $ freitag extract "03 - One Love - Bob Marley.mp3" --format "%tracknumber - %title - %artist.mp3"
    $ freitag get "03 - One Love - Bob Marley.mp3" --format "%artist - %title"
    Bob Marley - One Love

Don't forget to include the file extension in the extraction format!

Renaming
--------

You can rename your MP3s accorsing to their tags:

.. code-block:: shell

    $ freitag rename 01_-_bob_marley_-_one_love.mp3 --format="%tracknumber - %artist - %title.mp3"
    # 01 - Bob Marley - One Love.mp3

Remember to include the extension in the format.

Humanizing
----------

FreiTag can improve your song's tags removing underscores (_) and capitalizing
words.

.. code-block:: shell

    $ freitag get song.mp3 --format "%artist - %title"
    bob marley - One_love
    $ freitag humanize song.mp3
    $ freitag get song.mp3 --format "%artist - %title"
    Bob Marley - One Love

