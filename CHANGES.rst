0.5.1
   * drop Python 3.3 support. Although this module still works on Python 3.3, but it won't be tested anymore.

0.5.0
   * add FTS5 support. it works with both old and new FTS5 API. see https://sqlite.org/releaselog/3_20_0.html
   
0.4.9.2
   * use public API instead of accessing non public intefaces of SQLite objects. it requires libsqlite3.so/sqlite3.dll or equivalent again. see https://github.com/hideaki-t/sqlite-fts-python/issues/9
   * to allow SQLite3.11 and prior version, show a warning message instead of raise an error if it fails to enable 2 arg fts3_tokenizer.

0.4.9
   mainly for apsw
   
   * register_tokenizer expects a connection. it was ok to pass a sqlite3's cursor before, but it won't work any more.
   * fix a memory leak that can cause SEGV
   * it may work on environments that cannot use sqlite3_db_config to enable two argument version fts3_tokenizer (e.g. SQLite 3.11 and prior versions)
   * add unittest using apsw
