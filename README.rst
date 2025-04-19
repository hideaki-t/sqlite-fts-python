|build status|_

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

 * Python 2.7, Python 3.9+, and PyPy2.7, PyPy3.10+ (older versions may work, but not tested)

   * sqlite3 has to be dynamically linked. see GH-37_

 * CFFI_
 * FTS3/4 and/or FTS5 enabled SQLite3 or APSW_ (OS/Python bundled SQLite3 shared library may not work, building sqlite3 from source or pre-compiled binary may be required)

   * SQLite 3.11.x have to be compiled with -DSQLITE_ENABLE_FTS3_TOKENIZER to enable 2-arg fts3_tokenizer
   * SQLite older/newer than 3.11.x do not have extra requirements

Note for APSW users:
 * FTS3 should work as same as builtin sqlite3 - sqlite3(_sqlite3) is used to access SQLite internals
 * sqlitefts.fts5 does not support APSW Amalgamation build. see GH-14_

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
.. |build status| image:: https://github.com/hideaki-t/sqlite-fts-python/actions/workflows/package.yml/badge.svg
.. _build status: https://github.com/hideaki-t/sqlite-fts-python/actions/workflows/package.yml
.. _APSW: https://github.com/rogerbinns/apsw
.. _GH-14: https://github.com/hideaki-t/sqlite-fts-python/issues/14
.. _GH-37: https://github.com/hideaki-t/sqlite-fts-python/issues/37
