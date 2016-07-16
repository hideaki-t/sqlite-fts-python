sqlite-fts-python
=================

sqlitefts-python provides binding for tokenizer of `SQLite Full-Text search(FTS3/4)`_.
It allows you to write tokenizers in Python.


SQLite has Full-Text search feature FTS3/FTS4 along with some `predefined tokenizers`_.
It is easy to use and has enough functionality. Python has a built-in SQLite module,
so that it is easy to use and deploy. You don't need anything else to full-text search.

But... Predefined tokenizers are not enough for some languages including Japanese. Also it is not easy to write own tokenizers.
With this modules, you can write tokenizers in Python without any extra modules and C compiler.


Requirements
============

 * FTS3/4 enabled SQLite (for Windows, you may need to download and replace sqlite3.dll)


Licence
=======

This software is released under the MIT License, see LICENSE.


Thanks
======

 * https://github.com/saaj


.. _SQLite Full-Text search(FTS3/4): http://www.sqlite.org/fts3.html
.. _predefined tokenizers: http://www.sqlite.org/fts3.html#tokenizer
