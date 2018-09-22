|travisci build status|_
|appveyor build status|_

sqlitefts-python
================

sqlitefts-python provides binding for tokenizer of `SQLite Full-Text search(FTS3/4)`_ and `FTS5`_. it allows you to write tokenizers in Python.


SQLite has Full-Text search feature FTS3/FTS4 and FTS5 along with some `predefined tokenizers for FTS3/4`_, and also `predefined tokenizers for FTS5`_.
It is easy to use and has enough functionality. Python has a built-in SQLite module,
so that it is easy to use and deploy. You don't need anything else to full-text search.

But... the predefined tokenizers are not enough for some languages including Japanese. Also it is not easy to write own tokenizers.
This module provides ability to write tokenizers using Python with CFFI_, so that you don't need C compiler to write your tokenizer.

It also has ranking functions based on `peewee`_, utility function to add FTS5 auxiliary functions, and an FTS5 aux function implementation.

NOTE: all connections using this modules should be explicitly closed. due to GC behavior, it can be crashed if a connection is left open when a program terminated.

Sample tokenizer
----------------
There are differences between FTS3/4 and FTS5, so 2 different base classes are defined.

- a tokenizer for FTS3/4 can be used with FTS5 by using FTS3TokenizerAdaptor.
- a tokenizer for FTS5 can be used with FTS3/4 if 'flags' is not used.

FTS3/4::

  import sqlitefts as fts

  class SimpleTokenizer(fts.Tokenizer):
      _p = re.compile(r'\w+', re.UNICODE)

      def tokenize(self, text):
          for m in self._p.finditer(text):
              s, e = m.span()
              t = text[s:e]
              l = len(t.encode('utf-8'))
              p = len(text[:s].encode('utf-8'))
              yield t, p, p + l

  tk = sqlitefts.make_tokenizer_module(SimpleTokenizer())
  fts.register_tokenizer(conn, 'simple_tokenizer', tk)

FTS5::

  from sqlitefts import fts5

  class SimpleTokenizer(fts5.FTS5Tokenizer):
      _p = re.compile(r'\w+', re.UNICODE)

      def tokenize(self, text, flags=None):
          for m in self._p.finditer(text):
              s, e = m.span()
              t = text[s:e]
              l = len(t.encode('utf-8'))
              p = len(text[:s].encode('utf-8'))
              yield t, p, p + l

  tk = fts5.make_fts5_tokenizer(SimpleTokenizer())
  fts5.register_tokenizer(conn, 'simple_tokenizer', tk)

Requirements
============

 * Python 2.7, Python 3.3+, and PyPy2.7, PyPy3.2+
 * CFFI_
 * FTS3/4 and/or FTS5 enabled SQLite3 or APSW_ (for Windows, you may need to download and replace sqlite3.dll)

   * SQLite 3.11.x have to be compiled with -DSQLITE_ENABLE_FTS3_TOKENIZER to enable 2-arg fts3_tokenizer
   * SQLite 3.10.2 and older versions do not have extra requirements. 2-arg fts3_tokenizer is always avaiable.
   * SQLite 3.12.0 and later vesrions do not have extra requirements. 2-arg fts3_tokenizer can be enabled dynamically.

Note for APSW users: An APSW Amalgamation build does not expose SQLite APIs used in this module, so libsqlite3.so/sqlite3.dll is also required even it has no runtime library dependencies on SQLite. An APSW local build already depends on the shared library. Detail: sqlite3_db_config can be invoked via Connection.config, but it rejects SQLITE_DBCONFIG_ENABLE_FTS3_TOKENIZER to register a new tokenizer. tested at APSW 3.21.0-r1.

Licence
=======

This software is released under the MIT License, see LICENSE.


Thanks
======

 * https://github.com/saaj


.. _SQLite Full-Text search(FTS3/4): https://www.sqlite.org/fts3.html
.. _FTS5: https://www.sqlite.org/fts5.html
.. _predefined tokenizers for FTS3/4: https://www.sqlite.org/fts3.html#tokenizer
.. _predefined tokenizers for FTS5: https://www.sqlite.org/fts5.html#section_4_3
.. _peewee: https://github.com/coleifer/peewee
.. _CFFI: https://cffi.readthedocs.io/en/latest/
.. _ctypes: https://docs.python.org/library/ctypes.html
.. |travisci build status| image:: https://api.travis-ci.org/hideaki-t/sqlite-fts-python.svg?branch=master
.. _travisci build status: https://travis-ci.org/hideaki-t/sqlite-fts-python
.. |appveyor build status| image:: https://ci.appveyor.com/api/projects/status/github/hideaki-t/sqlite-fts-python?svg=true
.. _appveyor build status: https://ci.appveyor.com/project/hideaki-t/sqlite-fts-python
.. _APSW: https://github.com/rogerbinns/apsw
