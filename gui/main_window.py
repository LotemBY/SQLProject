import enum

import PySimpleGUI as sg

import db_manager
from gui.custom_tab import CustomTab
from gui.insert_book_tab import InsertBookTab
from gui.word_appearance_tab import WordAppearanceTab


class BookGUI:
    class KEYS(enum.Enum):
        WORDS_LIST = enum.auto(),
        APPR_TABLE = enum.auto(),

    def __init__(self):
        # Dark brown 1 | Dark Teal 10 | Dark grey 2
        sg.theme("Dark brown 1")
        sg.SetOptions(font=("Ariel", 12))

        self.window = sg.Window('Table', size=(1000, 800), finalize=True)
        self.db = db_manager.BookDatabase(db_path='books.db', always_create=True)

        self.insert_book_tab = InsertBookTab(self.db)
        self.word_appearance_tab = WordAppearanceTab(self.db)
        self.tabs = sg.TabGroup([[self.insert_book_tab, self.word_appearance_tab]])
        self.window.Layout([[self.tabs]])
        self.window.finalize()

        self.db.insert_book_to_db("Book",
                                  "Unknown",
                                  r"C:\Users\Lotem\Desktop\sql\example_book2.txt")
        self.insert_book_tab.update_books_table()

    def start(self):
        for row in self.tabs.Rows:
            for tab in row:
                tab.start()

        while True:
            event, values = self.window.read()
            print(event)

            if event is None:
                break
            else:
                curr_tab = self.window.Element(self.tabs.Get())  # type: CustomTab
                curr_tab.handle_event(event)

        self.db.commit()
        self.window.Close()
