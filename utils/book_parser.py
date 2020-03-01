import re

from utils.global_constants import VALID_WORD_REGEX
from utils.utils import cached_read

END_OF_LINE_REGEX = r"[\.?!]"


def parse_book(path):
    words_counter = 0
    paragraph_counter = 0
    between_paragraphs = True
    sentence_counter = 1
    words_in_sentence = 0

    # Go over the lines in the file
    raw = cached_read(path)
    for line_counter, line in enumerate(raw.split("\n"), 1):
        # Split each line to the different sentences
        words_in_line = 0
        sentence_offset_in_line = 0
        for sentence_number, sentence in enumerate(re.split(END_OF_LINE_REGEX, line)):
            if sentence_number > 0:
                # If its not the first sentence we parse in the line, start a new sentence
                words_in_sentence = 0
                sentence_counter += 1

            # Get the list of the words matches
            words_match = list(re.finditer(VALID_WORD_REGEX, sentence))

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
                    word = word_match[0]
                    words_in_line += 1
                    words_counter += 1
                    words_in_sentence += 1
                    line_offset = sentence_offset_in_line + word_match.start()

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
