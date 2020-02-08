SELECT word_id, name
FROM word NATURAL JOIN word_appearance
WHERE book_id like ?
GROUP BY word_id
order by name