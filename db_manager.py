import os
import sqlite3
import functools


class Database:
    SCRIPTS_DIR = "scripts"

    def __init__(self, db_path=None, always_create=False):
        if always_create and db_path and os.path.exists(db_path):
            os.remove(db_path)

        self._conn = sqlite3.connect(db_path if db_path else ':memory:')
        self.cursor = self._conn.cursor()

    @functools.lru_cache()
    def read_script_file(self, file_name):
        path = os.path.join(Database.SCRIPTS_DIR, file_name + '.sql')
        with open(path, 'r') as script_file:
            script_data = script_file.read()

        return script_data

    def run_sql_file(self, file_name, args=(), multiple_statements=False):
        script_data = self.read_script_file(file_name)

        if multiple_statements:
            return self.cursor.executescript(script_data)
        else:
            return self.cursor.execute(script_data, args)

    def commit(self):
        return self._conn.commit()

    def close(self, commit=True):
        if commit:
            self.commit()

        if self.cursor:
            self.cursor.close()

        if self._conn:
            self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self.close()


class BookDatabase(Database):
    INITIALIZE_SCHEMA = "initialize_schema"
    INSERT_BOOK = "insert_book"
    INSERT_WORD = "insert_word"
    INSERT_WORD_APPEARANCE = "insert_word_appearance"

    def initialize_schema(self):
        self.run_sql_file(BookDatabase.INITIALIZE_SCHEMA, multiple_statements=True)

    def insert_book(self, *args):
        return self.run_sql_file(BookDatabase.INSERT_BOOK, args)

    def insert_word(self, *args):
        return self.run_sql_file(BookDatabase.INSERT_WORD, args)

    def insert_word_appearance(self, *args):
        return self.run_sql_file(BookDatabase.INSERT_WORD_APPEARANCE, args)
