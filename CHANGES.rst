0.4.9
   mainly for apsw
   
   * register_tokenizer expects a connection. it was ok to pass a sqlite3's cursor before, but it won't work any more.
   * fix a memory leak that can cause SEGV
   * it may work on environments that cannot use sqlite3_db_config to enable two argument version fts3_tokenizer (e.g. SQLite 3.11 and prior versions)
   * add unittest using apsw
0.4.9.2
   * use public API instead of accessing non public intefaces of SQLite objects. it requires libsqlite3.so/sqlite3.dll or equivalent again. see https://github.com/hideaki-t/sqlite-fts-python/issues/9
   * to allow SQLite3.11 and prior version, show a warning message instead of raise an error if it fails to enable 2 arg fts3_tokenizer.
