0.4.9
   mainly for apsw
   
   * register_tokenizer expects a connection. it was ok to pass a sqlite3's cursor before, but it won't work any more.
   * fix a memory leak that can cause SEGV
   * it may work on environments that cannot use sqlite3_db_config to enable two argument version fts3_tokenizer (e.g. SQLite 3.11 and prior versions)
   * add unittest using apsw
