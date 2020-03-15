import functools
from enum import Enum, auto

import PySimpleGUI as sg

import gui.simple_gui_helper as sgh
from db.books_db import BookDatabase
from db.xml.export_db import build_xml, export_db
from gui.simple_gui_helper import WINDOW_SIZE
from gui.tabs.custom_tab import CustomTab
from gui.tabs.book_tab import BookTab
from gui.tabs.group_tab import GroupTab
from gui.tabs.phrase_tab import PhraseTab
from gui.tabs.statistics_tab import StatisticsTab
from gui.tabs.word_tab import WordTab


class BookGUI:
    class KEYS(Enum):
        NEW_BUTTON = auto()
        LOAD_BUTTON = auto()
        SAVE_BUTTON = auto()
        SAVE_AS_BUTTON = auto()
        EXPORT_BUTTON = auto()
        TABS = auto()

    TAB_CLASSES = (BookTab, WordTab, GroupTab, PhraseTab, StatisticsTab)

    UNSAVED_DATA_WARNING = "Continuing will delete all unsaved data.\n" \
                           "Do you wish to continue?\n"

    AUTO_SAVE_NOTICE = "Please Notice:\n" \
                       "All feature work will be saved to this file automatically."

    def __init__(self):
        sgh.config_theme()

        self.db = BookDatabase()  # db_path='books.db', always_create=True)
        self.window = sg.Window('Table', size=WINDOW_SIZE, finalize=True)

        self.tabs = sg.TabGroup([self.create_tabs()], key=BookGUI.KEYS.TABS, enable_events=True)

        self.callbacks = {
            BookGUI.KEYS.NEW_BUTTON: self.reset_database,
            BookGUI.KEYS.LOAD_BUTTON: self.load_database,
            BookGUI.KEYS.SAVE_BUTTON: functools.partial(self.save_database, True),
            BookGUI.KEYS.SAVE_AS_BUTTON: functools.partial(self.save_database, False),
            BookGUI.KEYS.EXPORT_BUTTON: self.export_database
        }

        self.window.layout([
            self._create_menu_buttons_row(),
            [self.tabs]
        ])

        self.window.finalize()
        self.window.TKroot.bind('<Return>', self.handle_enter)

    @staticmethod
    def _create_menu_buttons_row():
        new_button = sg.Button(
            button_text="New",
            key=BookGUI.KEYS.NEW_BUTTON
        )

        load_button = sg.Button(
            button_text="Load",
            key=BookGUI.KEYS.LOAD_BUTTON
        )

        save_button = sg.Button(
            button_text="Save",
            key=BookGUI.KEYS.SAVE_BUTTON
        )

        save_as_button = sg.Button(
            button_text="Save As",
            key=BookGUI.KEYS.SAVE_AS_BUTTON
        )

        export_button = sg.Button(
            button_text="Export",
            key=BookGUI.KEYS.EXPORT_BUTTON
        )

        return [new_button, load_button, save_button, save_as_button, export_button]

    def reset_database(self):
        if sg.popup_yes_no(self.UNSAVED_DATA_WARNING, title="New") == "Yes":
            self.db.new_connection()
            self.reload_tabs()

    def save_database(self, switch_to_new):
        path = sg.popup_get_file(
            message=None,
            no_window=True,
            save_as=True,
            file_types=(("Database", "*.db"), ("ALL Files", "*.*"))
        )

        if path:
            self.db.save_to_file(path, switch_to_new)

            if switch_to_new:
                sg.popup_ok(BookGUI.AUTO_SAVE_NOTICE,
                            title="Save")
            else:
                sg.popup_ok("Successfully saved a copy of the current work.",
                            title="Saved As")

    def load_database(self):
        if sg.popup_yes_no(self.UNSAVED_DATA_WARNING, title="Load") == "Yes":
            path = sg.PopupGetFile(
                message=None,
                no_window=True,
                file_types=(("Database", "*.db"), ("ALL Files", "*.*"))
            )

            if path:
                self.db.new_connection(db_path=path)
                self.reload_tabs()
                sg.popup_ok("Successfully loaded from file.",
                            BookGUI.AUTO_SAVE_NOTICE,
                            title="Load")

    def export_database(self):
        path = sg.popup_get_file(
            message=None,
            no_window=True,
            save_as=True,
            file_types=(("XML", "*.xml"), ("ALL Files", "*.*"))
        )

        if path:
            export_db(self.db, path)

    def create_tabs(self):
        return [tab_class(self.db) for tab_class in BookGUI.TAB_CLASSES]

    def initialize_tabs(self):
        for row in self.tabs.Rows:
            for tab in row:
                tab.initialize()

    def reload_tabs(self):
        for row in self.tabs.Rows:
            for tab in row:
                tab.reload_from_db()

    def DEBUG_init_db(self):
        self.db.insert_book_to_db("Book",
                                  "Unknown",
                                  r"C:\Users\Lotem\Desktop\sql\ideas.txt",
                                  "1/1/2000")

        self.db.insert_words_group("Animals")
        self.db.insert_words_group("Weird Words")

    def handle_enter(self, _key_event):
        curr_tab = self.window.Element(self.tabs.get())  # type: CustomTab
        curr_tab.handle_enter(self.window.find_element_with_focus())

    def start(self):
        self.initialize_tabs()
        self.DEBUG_init_db()

        while True:
            event = self.window.read()[0]
            # print(event, values)

            if event is None:
                break
            elif event in self.callbacks:
                self.callbacks[event]()

            curr_tab = self.window.Element(self.tabs.get())  # type: CustomTab
            curr_tab.handle_event(event)

        self.db.commit()
        self.window.close()
