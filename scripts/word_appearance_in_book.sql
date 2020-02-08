SELECT book_id, line_offset, paragraph, line, line_index, sentence, sentence_index
FROM word NATURAL JOIN word_appearance
WHERE book_id like ? AND word_id == ?