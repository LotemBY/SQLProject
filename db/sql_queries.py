"""
This files contains the different SQL queries used.
"""


#
# INSERT TO DATABASE
#

# language=SQL
INSERT_BOOK = """
INSERT INTO book(title, author, file_path, file_size, creation_date)
values (?, ?, ?, ?, ?);
"""

# language=SQL
INSERT_WORD = """
INSERT OR IGNORE INTO word(name, length)
values (?, ?);
"""

# language=SQL
INSERT_WORD_WITH_ID = """
INSERT INTO word(word_id, name)
values (?, ?);
"""

# language=SQL
INSERT_WORD_APPEARANCE = """
INSERT INTO word_appearance(book_id, word_id, word_index, paragraph, line, line_index, line_offset, sentence, sentence_index)
VALUES (?, (SELECT word_id FROM word WHERE name == ?), ?, ?, ?, ?, ?, ?, ?);
"""

# language=SQL
INSERT_WORD_ID_APPEARANCE = """
INSERT INTO word_appearance(book_id, word_id, word_index, paragraph, line, line_index, line_offset, sentence, sentence_index)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

# language=SQL
INSERT_WORDS_GROUP = """
INSERT INTO words_group(name)
values (?);
"""

# language=SQL
INSERT_WORD_TO_GROUP = """
INSERT INTO word_in_group(group_id, word_id)
values (?, ?);
"""

# language=SQL
INSERT_PHRASE = """
INSERT INTO phrase(phrase_text, words_count) VALUES (?, ?);
"""

# language=SQL
INSERT_WORD_TO_PHRASE = """
INSERT INTO word_in_phrase(phrase_id, word_id, phrase_index)
values (?, (SELECT word_id FROM word WHERE name == ?), ?);
"""

# language=SQL
INSERT_WORD_ID_TO_PHRASE = """
INSERT INTO word_in_phrase(phrase_id, word_id, phrase_index)
values (?, ?, ?);
"""

#
# SIMPLE QUERIES
#

# language=SQL
ALL_WORDS = "SELECT word_id, name " \
            "FROM word " \
            "ORDER BY name"

# language=SQL
ALL_BOOKS = "SELECT book_id, title, author, file_path, file_size, STRFTIME(?, creation_date) " \
            "FROM book"

# language=SQL
BOOK_ID_TO_TITLE = "SELECT title " \
                   "FROM book " \
                   "WHERE book_id == ?"

# language=SQL
BOOK_ID_TO_FULL_NAME = "SELECT title || ' by ' || author " \
                       "FROM book " \
                       "WHERE book_id == ?"

# language=SQL
BOOK_ID_TO_PATH = "SELECT file_path " \
                  "FROM book " \
                  "WHERE book_id == ?"

# language=SQL
ALL_BOOK_WORDS = "SELECT word_id, paragraph, sentence, line, line_offset " \
                 "FROM word_appearance " \
                 "WHERE book_id == ? " \
                 "ORDER BY word_index"

# language=SQL
WORD_NAME_TO_ID = "SELECT word_id " \
                  "FROM word " \
                  "WHERE name == ?"

# language=SQL
WORD_LOCATION_TO_OFFSET = "SELECT line, line_offset " \
                          "FROM word_appearance " \
                          "WHERE book_id == ? AND sentence == ? AND sentence_index == ?"

# language=SQL
WORD_LOCATION_TO_END_OFFSET = "SELECT line, line_offset + length " \
                              "FROM word_appearance NATURAL JOIN word " \
                              "WHERE book_id == ? AND sentence == ? AND sentence_index == ?"

# language=SQL
ALL_GROUPS = "SELECT group_id, name " \
             "FROM words_group"

# language=SQL
ALL_WORDS_IN_GROUP = "SELECT word_id, name " \
                     "FROM word NATURAL JOIN word_in_group " \
                     "WHERE group_id == ? " \
                     "ORDER BY name"

# language=SQL
ALL_PHRASES = "SELECT phrase_text, phrase_id " \
              "FROM phrase"

# language=SQL
ALL_WORDS_IN_PHRASE = "SELECT word_id " \
                      "FROM word_in_phrase " \
                      "WHERE phrase_id == ? " \
                      "ORDER BY phrase_index"

#
# STATISTICS
#

# language=SQL
BOOKS_COUNT = "SELECT COUNT(book_id) " \
              "FROM book"

# language=SQL
GROUPS_COUNT = "SELECT COUNT(group_id) " \
               "FROM words_group"

# language=SQL
PHRASES_COUNT = "SELECT COUNT(phrase_id) " \
                "FROM phrase"

# language=SQL
AVG_WORDS_PER_GROUP = """
SELECT AVG(words_count)
FROM 
    (SELECT COUNT(DISTINCT word_id) as words_count
    FROM word_in_group
    GROUP BY group_id)
"""

# language=SQL
AVG_WORDS_PER_PHRASE = """
SELECT AVG(words_count)
FROM 
    (SELECT COUNT(DISTINCT word_id) as words_count
    FROM word_in_phrase
    GROUP BY phrase_id)
"""

# language=SQL
TOTAL_SIZE = "SELECT SUM(file_size) " \
             "FROM book"

# language=SQL
TOTAL_WORDS = "SELECT COUNT(word_index) " \
              "FROM word_appearance " \
              "WHERE book_id {book_id_filter}"

# language=SQL
TOTAL_UNIQUE_WORDS = "SELECT COUNT(DISTINCT word_id) " \
                     "FROM word_appearance " \
                     "WHERE book_id {book_id_filter}"

# language=SQL
TOTAL_LETTERS = "SELECT SUM(length) " \
                "FROM word_appearance NATURAL JOIN word " \
                "WHERE book_id {book_id_filter}"

# language=SQL
AVG_LETTERS_PER_WORD = "SELECT AVG(length) " \
                       "FROM word_appearance NATURAL JOIN word " \
                       "WHERE book_id {book_id_filter}"

# language=SQL
TOTAL_COLUMN_COUNT = """
SELECT SUM(count_in_book) 
FROM 
    (SELECT COUNT(DISTINCT {count_column}) as count_in_book 
    FROM word_appearance 
    WHERE book_id {{book_id_filter}} 
    GROUP BY book_id)
"""

# language=SQL
WORDS_COUNT = """
SELECT AVG(words_count)
FROM 
    (SELECT COUNT(DISTINCT word_index) as words_count 
    FROM word_appearance 
    WHERE book_id {{book_id_filter}} 
    GROUP BY {count_column})
"""

# language=SQL
LETTERS_COUNT = """
SELECT AVG(letters_count)
FROM 
    (SELECT SUM(length) as letters_count
    FROM word_appearance NATURAL JOIN word
    WHERE book_id {{book_id_filter}}
    GROUP BY {count_column})
"""
