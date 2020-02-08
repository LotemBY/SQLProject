import os
import sqlite3
import time

from utils.book_parser import parse_book
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
        # self._create_book_trigger()
        self.book_insert_callbacks = []

    def _initialize_schema(self):
        self.run_sql_file(BookDatabase.SCRIPTS.INITIALIZE_SCHEMA, multiple_statements=True)

    def _create_book_trigger(self):
        self._conn.create_function("test", 0, self.notify_book_insert)
        self.cursor.execute("CREATE TRIGGER book_insertion AFTER INSERT ON book BEGIN SELECT test(); END;")

    def add_book_insert_callback(self, callback):
        self.book_insert_callbacks.append(callback)

    def notify_book_insert(self):
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

    def insert_book_to_db(self, title, author, path):
        if not os.path.exists(path):
            raise FileNotFoundError

        # TODO: Copy the file to my own dir?

        try:
            self.insert_book(title, author, path, time.time())
        except sqlite3.IntegrityError:
            return False

        for word in parse_book(path):
            (word, word_index, paragraph_index, line_index, index_in_line, offset_in_line, sentence_index,
             index_in_sentence) = word
            self.insert_word(word)
            self.insert_word_appearance(word_index,
                                        title,
                                        word,
                                        paragraph_index,
                                        line_index,
                                        index_in_line,
                                        offset_in_line,
                                        sentence_index,
                                        index_in_sentence)

        self.notify_book_insert()
        return True

    def query_words_in_book(self, book_id):
        return self.run_sql_file(BookDatabase.SCRIPTS.WORDS_IN_BOOK, (book_id,))

    def query_words_appearance_in_book(self, book_id, word_id):
        return self.run_sql_file(BookDatabase.SCRIPTS.WORD_APPEARANCE_IN_BOOK, (book_id, word_id))

    def search_word_appearances(self, cols, tables=None, unique_words=False, order_by=None, **kwargs):
        query = f'SELECT {", ".join(cols)} FROM word_appearance'

        for table in tables:
            query += ' NATURAL JOIN ' + table

        constraints = []
        for col_name, value in kwargs.items():
            if value is not None:
                constraints.append(f'{col_name} == {value}')
        if constraints:
            query += ' WHERE ' + ' AND '.join(constraints)

        if unique_words:
            query += ' GROUP BY word_id'

        if order_by:
            query += ' ORDER BY ' + order_by

        print(query)
        return self.cursor.execute(query)  # Using new cursor since this is happening in a trigger
