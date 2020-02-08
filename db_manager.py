import functools
import os
import sqlite3

from utils.utils import cached_read


class Database:
    SCRIPTS_DIR = "scripts"

    def __init__(self, db_path=None, always_create=False):
        if always_create and db_path and os.path.exists(db_path):
            os.remove(db_path)

        self._conn = sqlite3.connect(db_path if db_path else ':memory:')
        self.cursor = self.new_cursor()

    def new_cursor(self):
        return self._conn.cursor()

    def read_script_file(self, file_name):
        path = os.path.join(Database.SCRIPTS_DIR, file_name + '.sql')
        return cached_read(path)

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


def test(x):
    print(x)


class BookDatabase(Database):
    class SCRIPTS:
        INITIALIZE_SCHEMA = "initialize_schema"
        INSERT_BOOK = "insert_book"
        INSERT_WORD = "insert_word"
        INSERT_WORD_APPEARANCE = "insert_word_appearance"
        WORDS_IN_BOOK = "words_in_book"
        WORD_APPEARANCE_IN_BOOK = "word_appearance_in_book"

    def __init__(self, **kargs):
        super().__init__(**kargs)
        self._initialize_schema()
        self._create_book_trigger()
        self.book_insert_callbacks = []

    def _initialize_schema(self):
        self.run_sql_file(BookDatabase.SCRIPTS.INITIALIZE_SCHEMA, multiple_statements=True)

    def _create_book_trigger(self):
        self._conn.create_function("test", 0, self.book_insert_callback)
        self.cursor.execute("CREATE TRIGGER book_insertion AFTER INSERT ON book BEGIN SELECT test(); END;")

    def add_book_insert_callback(self, callback):
        self.book_insert_callbacks.append(callback)

    def book_insert_callback(self):
        for callback in self.book_insert_callbacks:
            callback()

    def insert_book(self, title, author, path, time):
        return self.run_sql_file(BookDatabase.SCRIPTS.INSERT_BOOK, (title, author, path, time))

    def insert_word(self, word):
        return self.run_sql_file(BookDatabase.SCRIPTS.INSERT_WORD, (word,))

    def insert_word_appearance(self, word_index, book_id, word_id, paragraph, line, line_index, line_offset, sentence,
                               sentence_index):
        return self.run_sql_file(BookDatabase.SCRIPTS.INSERT_WORD_APPEARANCE, (
            word_index, book_id, word_id, paragraph, line, line_index, line_offset, sentence, sentence_index))

    def query_words_in_book(self, book_id):
        return self.run_sql_file(BookDatabase.SCRIPTS.WORDS_IN_BOOK, (book_id,))

    def query_words_appearance_in_book(self, book_id, word_id):
        return self.run_sql_file(BookDatabase.SCRIPTS.WORD_APPEARANCE_IN_BOOK, (book_id, word_id))
