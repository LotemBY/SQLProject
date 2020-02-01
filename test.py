# import ui
from book_parser import insert_book_to_db
from db_manager import BookDatabase

BOOKS = [r"C:\Users\Lotem\Desktop\sql\example_book2.txt", r"C:\Users\Lotem\Desktop\sql\LOTR.txt"]


def test():
    with BookDatabase("test.db", always_create=True) as db:  # type: BookDatabase
        db.initialize_schema()
        for book_path in BOOKS:
            insert_book_to_db(db, book_path)

        print_most_common_words(db)


def print_most_common_words(db: BookDatabase):
    for word, word_id, count in db.run_sql_file("common_words"):
        print('%6s %12s | %d' % (f'({word_id})', word, count))


# def gui_test():
#     ui.start()


if __name__ == '__main__':
    test()
    # gui_test()
