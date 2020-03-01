from enum import Enum, auto

import PySimpleGUI as sg

import gui.simple_gui_helper as sgh
from db import books_db
from gui.simple_gui_helper import WINDOW_SIZE
from gui.custom_tab import CustomTab
from gui.insert_book_tab import InsertBookTab
from gui.insert_group_tab import InsertGroupTab
from gui.word_appearance_tab import WordAppearanceTab


class BookGUI:
    class KEYS(Enum):
        TABS = auto()

    TAB_CLASSES = (InsertBookTab, WordAppearanceTab, InsertGroupTab)

    def __init__(self):
        sgh.config_theme()

        self.db = books_db.BookDatabase(db_path='books.db', always_create=True)
        self.window = sg.Window('Table', size=WINDOW_SIZE, finalize=True)

        tab_list = self.create_tabs()
        self.insert_book_tab = tab_list[0]
        self.tabs = sg.TabGroup([tab_list], key=BookGUI.KEYS.TABS, enable_events=True)
        self.window.Layout([[self.tabs]])
        self.window.finalize()

        self.window.TKroot.bind('<Return>', self.handle_enter)

    def create_tabs(self):
        return [tab_class(self.db) for tab_class in BookGUI.TAB_CLASSES]

    def DEBUG_init_db(self):
        self.db.insert_book_to_db("Book",
                                  "Unknown",
                                  r"C:\Users\Lotem\Desktop\sql\ideas.txt")
        self.insert_book_tab.update_books_table()

        self.db.insert_words_group("Animals")
        self.db.insert_words_group("Weird Words")

    def handle_enter(self, _key_event):
        curr_tab = self.window.Element(self.tabs.Get())  # type: CustomTab
        curr_tab.handle_enter(self.window.find_element_with_focus())

    def start(self):
        for row in self.tabs.Rows:
            for tab in row:
                tab.initialize()

        self.DEBUG_init_db()

        while True:
            event, values = self.window.read()
            print(event, values)

            if event is None:
                break

            curr_tab = self.window.Element(self.tabs.Get())  # type: CustomTab
            curr_tab.handle_event(event)

        self.db.commit()
        self.window.Close()
