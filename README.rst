|codeship build status|_
|appveyor build status|_


================

sqlitefts-python provides binding for tokenizer of `SQLite Full-Text search(FTS3/4)`_.
It allows you to write tokenizers in Python.


SQLite has Full-Text search feature FTS3/FTS4 along with some `predefined tokenizers`_.
It is easy to use and has enough functionality. Python has a built-in SQLite module,
so that it is easy to use and deploy. You don't need anything else to full-text search.

But... the predefined tokenizers are not enough for some languages including Japanese. Also it is not easy to write own tokenizers.
This module provides ability to write your own tokenizers using Python without C compiler by CFFI_.

It also has ranking functions based on `peewee`_.

NOTE: all connections using this modules should be explicitly closed. due to GC behavior, it can be crashed if a connection is left open when a program terminated.

============

 * Python 2.7, Python 3.3+, and PyPy2.7, PyPy3.2+
 * CFFI_
 * FTS3/4 enabled SQLite3 or APSW_ (for Windows, you may need to download and replace sqlite3.dll)
   * SQLite 3.11.x have to be compiled with -DSQLITE_ENABLE_FTS3_TOKENIZER to enable 2-arg fts3_tokenizer
   * SQLite 3.10.2 and older versions do not have extra requirements. 2-arg fts3_tokenizer is always avaiable.
   * SQLite 3.12.0 and later vesrions do not have extra requirements. 2-arg fts3_tokenizer can be enabled dynamically.

=======

This software is released under the MIT License, see LICENSE.


======

 * https://github.com/saaj


.. _SQLite Full-Text search(FTS3/4): http://www.sqlite.org/fts3.html
.. _predefined tokenizers: http://www.sqlite.org/fts3.html#tokenizer
.. _peewee: https://github.com/coleifer/peewee
.. _CFFI: http://cffi.readthedocs.io/en/latest/
.. _ctypes: https://docs.python.org/library/ctypes.html
.. |codeship build status| image:: https://codeship.com/projects/fc2fe0d0-33d2-0134-50c3-7e300f67430e/status?branch=master
.. _codeship build status: https://codeship.com/projects/164859
.. |appveyor build status| image:: https://ci.appveyor.com/api/projects/status/github/hideaki-t/sqlite-fts-python?svg=true
.. _appveyor build status: https://ci.appveyor.com/project/hideaki-t/sqlite-fts-python
.. _APSW: https://github.com/rogerbinns/apsw
