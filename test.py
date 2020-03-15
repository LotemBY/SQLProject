import time
from datetime import datetime

from db.books_db import BookDatabase
from db.query_builder import build_query
from db.xml.export_db import export_db

BOOKS = [r"C:\Users\Lotem\Desktop\sql\example_book2.txt", r"C:\Users\Lotem\Desktop\sql\LOTR.txt"]


def print_most_common_words(db: BookDatabase):
    for word, word_id, count in db.run_sql_file("common_words"):
        print('%6s %12s | %d' % (f'({word_id})', word, count))


def init_test_db():
    db = BookDatabase(db_path='test_books.db', always_create=True)
    # db.insert_book_to_db("Ideas", "Lotem", r"C:/Users/Lotem/Desktop/sql/ideas.txt")
    return db


def phrase_test(db: BookDatabase):
    phrase_id = db.create_phrase("a b")

    print("Searching phrase.")

    sum = 0
    for _ in range(10):
        start = time.time()
    print(db.find_phrase(phrase_id))
    end = time.time()

    print(f"That took {end - start} seconds!")
    sum += end - start
    print(f'Avg: {sum / 10} seconds.')


def statistics(db, book_id):
    print("Total Words: " + str(db.search_word_appearances(
        cols=["COUNT(word_index)"],
        book_id=book_id
    )[0][0]))

    print("Total Unique Words: " + str(db.search_word_appearances(
        cols=["COUNT(DISTINCT word_id)"],
        book_id=book_id
    )[0][0]))

    print("Total Letters: " + str(db.search_word_appearances(
        cols=["SUM(length)"],
        tables=["word"],
        book_id=book_id
    )[0][0]))

    print("Avg Letters per word: " + str(db.search_word_appearances(
        cols=["AVG(length)"],
        tables=["word"],
        book_id=book_id
    )[0][0]))

    for search_category in "paragraph", "line", "sentence":
        print(f"Total {search_category}s: " + str(db.build_and_exec_query(
            cols=["SUM(amount_per_book)"],
            tables=[build_query(
                cols=[f"COUNT(DISTINCT {search_category}) as amount_per_book"],
                tables=["word_appearance"],
                book_id=book_id,
                group_by="book_id"
            )]
        )))

        print(f"Avg Words per {search_category}: " + str(db.build_and_exec_query(
            cols=["AVG(words_count)"],
            tables=[build_query(
                cols=["COUNT(DISTINCT sentence_index) as words_count"],
                tables=["word_appearance"],
                group_by=search_category,
                book_id=book_id
            )]
        )))

        print(f"Avg Letters per {search_category}: " + str(db.build_and_exec_query(
            cols=["AVG(letters_count)"],
            tables=[build_query(
                cols=["SUM(length) as letters_count"],
                tables=["word_appearance", "word"],
                group_by=search_category,
                book_id=book_id
            )]
        )))


if __name__ == '__main__':
    db = init_test_db()

    print("Inserting book.")
    # book_id1 = db.insert_book_to_db("lotr", "Lotem", r"C:\Users\Lotem\Desktop\sql\LOTR.txt", datetime.now())
    book_id2 = db.insert_book_to_db("Phrases", "Lotem", r"C:\Users\Lotem\Desktop\sql\phrase_test.txt", datetime.now())
    book_id2 = db.insert_book_to_db("Book1", "Lotem", r"C:\Users\Lotem\Desktop\sql\book1.txt", datetime.now())

    group1 = db.insert_words_group("My group 1")
    group2 = db.insert_words_group("My group 2")

    for i in range(10):
        db.insert_word_to_group(group1, f"word1{i}")
        db.insert_word_to_group(group2, f"word2{i}")

    db.create_phrase("Wow this is an actual phrase!")
    db.create_phrase("And this is another phrase omg")

    print("Dumping...")
    export_db(db, "test.xml")
    db.commit()

    exit(0)

    print("Creating phrase.")
    db.commit()
