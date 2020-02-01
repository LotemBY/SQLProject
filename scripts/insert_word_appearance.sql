INSERT INTO word_appearance(word_index, book_id, word_id, paragraph, line, line_index, sentence, sentence_index, offset)
VALUES
    (?,
    (SELECT book_id
        FROM book
        WHERE name == ?),
    (SELECT word_id
        FROM word
        WHERE name == ?),
    ?, ?, ?, ?, ?, ?);