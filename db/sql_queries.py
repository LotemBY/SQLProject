#
# INSERT TO DATABASE
#

# language=SQL
INSERT_BOOK = """
INSERT INTO book(title, author, file_path) --, creation_date)
values (?, ?, ?); --, datetime(?, 'unixepoch'));
"""

# language=SQL
INSERT_WORD = """
INSERT INTO word(name)
values (?);
"""

# language=SQL
INSERT_WORD_APPEARANCE = """
INSERT INTO word_appearance(word_index, book_id, word_id, paragraph, line, line_index, line_offset, sentence, sentence_index)
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
INSERT INTO phrase(words_count) VALUES (?);
"""

# language=SQL
INSERT_WORD_TO_PHRASE = """
INSERT INTO word_in_phrase(phrase_id, word_id, phrase_index)
values (?, ?, ?);
"""

#
# SIMPLE QUERIES
#

# language=SQL
ALL_BOOKS = "SELECT book_id, title, author FROM book"

# language=SQL
BOOK_ID_TO_PATH = "SELECT file_path FROM book WHERE book_id == ?"

# language=SQL
WORD_NAME_TO_ID = "SELECT word_id FROM word WHERE name == ?"

# language=SQL
ALL_GROUPS = "SELECT * FROM words_group"

# language=SQL
ALL_WORDS_IN_GROUP = "SELECT name FROM word NATURAL JOIN word_in_group WHERE group_id == ? ORDER BY name"
