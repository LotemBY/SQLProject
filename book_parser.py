import os
import re
import time
from os.path import splitext, split

from db_manager import BookDatabase

WORD_REGEX = r"(^|\W|'|\")(\w+([\w']*\w+)?)"


def parse_book(path):
    with open(path, 'r') as book_file:
        words_counter = 0
        line_offset_in_file = 0
        paragraph_counter = 0
        between_paragraphs = True
        sentence_counter = 1
        words_in_sentence = 0

        # Go over the lines in the file
        for line_counter, line in enumerate(book_file, 1):
            # Split each line to the different sentences
            words_in_line = 0
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

                        # The word offset is <offset of the start of the line> + <offset of the word inside the line>
                        word_offset = line_offset_in_file + word_match.start(2)
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
                               sentence_counter,
                               words_in_sentence,
                               word_offset)
                else:
                    # If there are no words, we are in between paragraphs
                    between_paragraphs = True
            # Add the length of the line to the total offset counter
            line_offset_in_file += len(line)


def insert_book_to_db(db: BookDatabase, book_path):
    book_name = splitext(split(book_path)[-1])[0]
    db.insert_book(book_name, "Lotem", book_path, time.time())

    for word in parse_book(book_path):
        (word, word_index, paragraph_index, line_index, index_in_line, sentence_index, index_in_sentence, offset) = word
        db.insert_word(word)
        db.insert_word_appearance(word_index,
                                  book_name,
                                  word,
                                  paragraph_index,
                                  line_index,
                                  index_in_line,
                                  sentence_index,
                                  index_in_sentence,
                                  offset)
