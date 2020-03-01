import functools
import os
import re
import sqlite3
import time

import db.sql_queries as queries
from db.db_manager import Database
from db.exceptions import CheckError, raise_specific_exception
from db.query_builder import build_query
from utils.book_parser import parse_book
from utils.global_constants import VALID_WORD_REGEX


class BookDatabase(Database):
    WORD_IDS_CACHE_SIZE = 1000
    VALID_MULTIPLE_WORDS = rf"{VALID_WORD_REGEX}(\W+{VALID_WORD_REGEX})*"
    INVALID_GROUP_NAMES = ["None", "All"]

    class SCRIPTS:
        INITIALIZE_SCHEMA = "initialize_schema"
        SEARCH_PHRASE = "search_phrase"

    def __init__(self, **kargs):
        super().__init__(**kargs)
        self._initialize_schema()
        self.book_insert_callbacks = []
        self.group_insert_callbacks = []
        self.group_word_insert_callbacks = []

    def _initialize_schema(self):
        self.run_sql_file(BookDatabase.SCRIPTS.INITIALIZE_SCHEMA, multiple_statements=True)

    def add_book_insert_callback(self, callback):
        self.book_insert_callbacks.append(callback)

    def add_group_insert_callback(self, callback):
        self.group_insert_callbacks.append(callback)

    def add_group_word_insert_callback(self, callback):
        self.group_word_insert_callbacks.append(callback)

    @staticmethod
    def call_all_callbacks(callbacks, *args):
        for callback in callbacks:
            callback(*args)

    @staticmethod
    def assert_valid_word(word):
        if not re.fullmatch(VALID_WORD_REGEX, word):
            raise CheckError

    @staticmethod
    def to_single_word(word):
        single_word = word.lower().strip()
        BookDatabase.assert_valid_word(single_word)
        return single_word

    @staticmethod
    def assert_valid_title(words):
        valid = re.fullmatch(BookDatabase.VALID_MULTIPLE_WORDS, words) and \
                words == words.title()

        if not valid:
            raise CheckError

    @staticmethod
    def to_title(words):
        title = words.title().strip()
        BookDatabase.assert_valid_title(title)
        return title

    # TODO: remove time or not?
    def insert_book(self, title, author, path, _time):
        return self.execute(queries.INSERT_BOOK,
                            (self.to_title(title), self.to_title(author), path)).lastrowid  # , time))

    def insert_word(self, word):
        return self.execute(queries.INSERT_WORD, (self.to_single_word(word),)).lastrowid

    # Will be used a lot for the same words, so caching the result can improve performance
    @functools.lru_cache(WORD_IDS_CACHE_SIZE)
    def get_word_id(self, word):
        """
        Return the word_id of a word.
        It that word doesn't have and id, it will be added to the db.
        :param word: The word to search for
        :return: The word_id of the word
        """

        word = self.to_single_word(word)

        # Most of the words we'll search for will already be inserted.
        # So we should first search for the word, and only try to insert it if it doesn't exists,
        # and not the other way around.
        search_result = self.execute(queries.WORD_NAME_TO_ID, (word,)).fetchone()

        return self.insert_word(word) if search_result is None else search_result[0]

    def insert_word_appearance(self, word_index, book_id, word_id, paragraph, line, line_index, line_offset, sentence,
                               sentence_index):
        return self.execute(queries.INSERT_WORD_APPEARANCE,
                            (word_index, book_id, word_id, paragraph, line,
                             line_index, line_offset, sentence, sentence_index)).lastrowid

    def insert_words_group(self, name):
        name = self.to_title(name)
        if name in BookDatabase.INVALID_GROUP_NAMES:
            raise CheckError

        group_id = self.execute(queries.INSERT_WORDS_GROUP, (name,)).lastrowid
        self.call_all_callbacks(self.group_insert_callbacks)
        return group_id

    def insert_word_to_group(self, group_id, word):
        rowid = self.execute(queries.INSERT_WORD_TO_GROUP, (group_id, self.get_word_id(word))).lastrowid
        self.call_all_callbacks(self.group_word_insert_callbacks, group_id)
        return rowid

    def insert_phrase(self, words_count):
        phrase_id = self.execute(queries.INSERT_PHRASE, (words_count,)).lastrowid
        # self.call_all_callbacks(self.phrase_insert_callbacks)am
        return phrase_id

    def insert_word_to_phrase(self, phrase_id, word, phrase_index):
        self.execute(queries.INSERT_WORD_TO_PHRASE, (phrase_id, self.get_word_id(word), phrase_index))

    def create_phrase(self, words):
        phrase_id = self.insert_phrase(len(words))
        for index, word in enumerate(words, start=1):
            self.insert_word_to_phrase(phrase_id, word, index)

        return phrase_id

    def insert_book_to_db(self, title, author, path):
        if not os.path.exists(path):
            raise FileNotFoundError

        # TODO: Copy the file to my own dir?
        book_id = self.insert_book(title, author, path, time.time())

        for word_appearance in parse_book(path):
            (word,
             word_index,
             paragraph_index,
             line_index,
             index_in_line,
             offset_in_line,
             sentence_index,
             index_in_sentence) = word_appearance

            self.insert_word_appearance(word_index,
                                        book_id,
                                        self.get_word_id(word),
                                        paragraph_index,
                                        line_index,
                                        index_in_line,
                                        offset_in_line,
                                        sentence_index,
                                        index_in_sentence)

        self.commit()
        self.call_all_callbacks(self.book_insert_callbacks)
        return book_id

    def build_and_exec_query(self, **kwargs):
        return self.execute(build_query(**kwargs)).fetchall()

    def search_books(self, tables=None, **kwargs):
        tables = set(tables) if tables else set()
        tables.add("book")
        return self.build_and_exec_query(cols=["book_id", "title", "author", "file_path"],
                                         tables=tables,
                                         group_by="book_id",
                                         **kwargs)

    def search_word_appearances(self, cols=None, tables=None, unique_words=False, order_by=None, **kwargs):
        tables = set(tables) if tables else set()
        tables.add("word_appearance")
        group_by = "word_id" if unique_words else None
        return self.build_and_exec_query(cols=cols,
                                         tables=tables,
                                         group_by=group_by,
                                         order_by=order_by,
                                         **kwargs)

    def all_books(self):
        return self.execute(queries.ALL_BOOKS).fetchall()

    def get_book_path(self, book_id):
        return self.execute(queries.BOOK_ID_TO_PATH, (book_id,)).fetchone()

    def all_groups(self):
        return self.execute(queries.ALL_GROUPS).fetchall()

    def words_in_group(self, group_id):
        return self.execute(queries.ALL_WORDS_IN_GROUP, (group_id,)).fetchall()

    def get_word_in_phrase(self, phrase_id, phrase_index):
        return self.execute("SELECT word_id FROM word_in_phrase WHERE phrase_id = ? AND phrase_index = ?",
                            (phrase_id, phrase_index)).fetchone()

    def find_phrase(self, book_id, phrase_id):
        return self.run_sql_file(BookDatabase.SCRIPTS.SEARCH_PHRASE, (book_id, phrase_id)).fetchall()
