INSERT INTO word_appearance(word_index, book_id, word_id, paragraph, line, line_index, line_offset, sentence, sentence_index)
VALUES
    (?,
    (SELECT book_id
        FROM book
        WHERE title == ?),
    (SELECT word_id
        FROM word
        WHERE name == ?),
    ?, ?, ?, ?, ?, ?);