import os
import re
import time
from sqlite3 import IntegrityError

from db_manager import BookDatabase

WORD_REGEX = r"(^|\W|'|\")(\w+([\w']*\w+)?)"


def parse_book(path):
    with open(path, 'r') as book_file:
        words_counter = 0
        sentence_offset_in_line = 0
        paragraph_counter = 0
        between_paragraphs = True
        sentence_counter = 1
        words_in_sentence = 0

        # Go over the lines in the file
        for line_counter, line in enumerate(book_file, 1):
            # Split each line to the different sentences
            words_in_line = 0
            sentence_offset_in_line = 0
            for sentence_number, sentence in enumerate(line.split(".")):
                if sentence_number > 0:
                    # If its not the first sentence we parse in the line, start a new sentence
                    words_in_sentence = 0
                    sentence_counter += 1

                # Get the list of the words matches
                words_match = list(re.finditer(WORD_REGEX, sentence))

                # Check if there are words in this line
                if words_match:
                    # If the last line was between paragraphs, we should start a new paragraph
                    if between_paragraphs:
                        paragraph_counter += 1
                        between_paragraphs = False

                        # If the last sentence wasn't ended by a dot '.', we should start a new sentence manually
                        if words_in_sentence > 0:
                            words_in_sentence = 0
                            sentence_counter += 1

                    # Go over the matched words and insert them to the database
                    for word_match in words_match:
                        word = word_match[2].lower()
                        words_in_line += 1
                        words_counter += 1
                        words_in_sentence += 1
                        line_offset = sentence_offset_in_line + word_match.start(2)

                        # print(' | '.join(
                        #     [f'#{words_counter}',
                        #      f'P{paragraph_counter}',
                        #      f'L{line_counter}',
                        #      f'LI{words_in_line}',
                        #      f'S{sentence_counter}',
                        #      f'SI{words_in_sentence}',
                        #      f'O{word_offset}',
                        #      f'"{word}"']))

                        yield (word,
                               words_counter,
                               paragraph_counter,
                               line_counter,
                               words_in_line,
                               line_offset,
                               sentence_counter,
                               words_in_sentence)
                else:
                    # If there are no words, we are in between paragraphs
                    between_paragraphs = True

                # Add the length of the line to the total offset counter
                sentence_offset_in_line += len(sentence) + 1


def insert_book_to_db(db: BookDatabase, title, author, path):
    if not os.path.exists(path):
        raise FileNotFoundError

    # TODO: Copy the file to my own dir?

    try:
        db.insert_book(title, author, path, time.time())
    except IntegrityError:
        return False

    for word in parse_book(path):
        (word, word_index, paragraph_index, line_index, index_in_line, offset_in_line, sentence_index,
         index_in_sentence) = word
        db.insert_word(word)
        db.insert_word_appearance(word_index,
                                  title,
                                  word,
                                  paragraph_index,
                                  line_index,
                                  index_in_line,
                                  offset_in_line,
                                  sentence_index,
                                  index_in_sentence)

    return True
