import time
from timeit import timeit

from db.books_db import BookDatabase

BOOKS = [r"C:\Users\Lotem\Desktop\sql\example_book2.txt", r"C:\Users\Lotem\Desktop\sql\LOTR.txt"]


def print_most_common_words(db: BookDatabase):
    for word, word_id, count in db.run_sql_file("common_words"):
        print('%6s %12s | %d' % (f'({word_id})', word, count))


def init_test_db():
    db = BookDatabase(db_path='test_books.db', always_create=True)
    db.insert_book_to_db("Ideas", "Lotem", r"C:/Users/Lotem/Desktop/sql/ideas.txt")
    return db


def phrase_test(db: BookDatabase, book_id):
    print("Phrase stuff")
    phrase_id = db.create_phrase("they had to wait".split(" "))
    print(db.find_phrase(book_id, phrase_id))


if __name__ == '__main__':
    db = init_test_db()

    print("Inserting book.")
    book_id = db.insert_book_to_db("lotr", "Lotem", r"C:\Users\Lotem\Desktop\sql\LOTR.txt")
    # book_id = db.insert_book_to_db("Phrases", "Lotem", r"C:\Users\Lotem\Desktop\sql\phrase_test.txt")

    # phrase_test(db, book_id)

    print("Creating phrase.")
    phrase_id = db.create_phrase("they had to wait".split(" "))

    print("Searching phrase.")

    sum = 0
    for _ in range(10):
        start = time.time()
        print(db.find_phrase(book_id, phrase_id))
        end = time.time()

        print(f"That took {end - start} seconds!")
        sum += end - start
    print(f'Avg: {sum / 10} seconds.')

    db.commit()
