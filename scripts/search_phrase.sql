SELECT sentence, sentence_index AS start_index, sentence_index + words_count - 1 AS end_index
FROM phrase NATURAL JOIN word_in_phrase NATURAL JOIN
    (SELECT sentence, sentence_index, word_id,
        sentence_index - ROW_NUMBER() OVER (PARTITION BY sentence ORDER BY sentence_index) AS consecutive_phrase_words
    FROM word_appearance NATURAL JOIN word_in_phrase
    WHERE book_id == ? AND phrase_id == ?
	GROUP BY sentence, sentence_index)
GROUP BY sentence, consecutive_phrase_words, phrase_index - sentence_index
HAVING COUNT(sentence_index) == words_count
ORDER BY sentence, sentence_index