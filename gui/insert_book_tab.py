import re
from enum import Enum, auto
from os.path import splitext, split
from subprocess import Popen

import PySimpleGUI as sg

import gui.simple_gui_helper as sgh
from db.exceptions import NonUniqueError, CheckError
from gui.custom_tab import CustomTab


class InsertBookTab(CustomTab):
    AUTHOR_REGEX = r"Author: (.+)$"
    TITLE_REGEX = r"Title: (.+)$"

    class KEYS(Enum):
        FILE_INPUT = auto()
        CONFIRM = auto()
        UPDATE_FILTER = auto()
        BOOKS_TABLE = auto()
        OPEN_BOOK = auto()

    def __init__(self, db):
        super().__init__(db, "Insert Book", [[]])
        self.db.add_book_insert_callback(self.update_books_table)

        self.filters = {}
        self.selected_book_id = None

        self.Layout([
            [self._create_book_form_frame()],
            [sg.Sizer(v_pixels=30)],
            [self._create_books_explorer_frame()]
        ])

    def _create_book_form_frame(self):
        self.file_input = sg.InputText(enable_events=True, key=InsertBookTab.KEYS.FILE_INPUT)
        self.browse_button = sg.FileBrowse(file_types=(("Text files", "*.txt"), ("All Files", "*")))
        self.title_input = sg.InputText()
        self.author_input = sg.InputText()

        self.file_size_text = sg.Text("File size: None", auto_size_text=False)

        insert_book_button = sg.Ok("Insert Book", key=InsertBookTab.KEYS.CONFIRM, size=(20, 0))
        self.response_text = sg.Text("", text_color=sgh.ERROR_TEXT_COLOR, auto_size_text=False)

        frame = sg.Frame(
            title="Insert New Book",
            layout=[
                [sg.Text("Path:", size=(5, 1)), self.file_input, self.browse_button],
                [sg.Text("Title:", size=(5, 1)), self.title_input],
                [sg.Text("Author:", size=(5, 1)), self.author_input],
                [self.file_size_text],
                [insert_book_button, self.response_text]
            ]
        )

        return frame

    def _create_books_filter_row(self):
        def _create_filter_input():
            return sg.InputText(
                default_text="",
                size=(20, 1),
                enable_events=True,
                key=InsertBookTab.KEYS.UPDATE_FILTER
            )

        row = []
        self.str_filters = []
        for text, filter_name in ("Title", "title"), ("Author", "author"), ("Word Appearance", "name"):
            element = _create_filter_input()
            row += [sg.Text(f"{text}: ", pad=((20, 5), 10)), element]
            self.str_filters.append((filter_name, element))

        return row

    def _create_books_explorer_frame(self):
        self.books_table = sg.Table(
            values=[],
            headings=["Book ID", "Title", "Author", "Path"],
            num_rows=15,
            justification=sg.TEXT_LOCATION_LEFT,
            col_widths=[0, 20, 20, 40],
            auto_size_columns=False,
            enable_events=True,
            visible_column_map=[False, True, True, True],
            key=InsertBookTab.KEYS.BOOKS_TABLE
        )

        open_book_button = sg.Button("Open Selected Book", key=InsertBookTab.KEYS.OPEN_BOOK)

        frame = sg.Frame(
            title="Books Explorer",
            layout=[
                self._create_books_filter_row(),
                [sg.Sizer(v_pixels=10)],
                [self.books_table],
                [sg.Sizer(v_pixels=70, h_pixels=650), open_book_button]
            ],
            element_justification=sgh.CENTER, pad=(10, 10)
        )

        return frame

    def initialize(self):
        self.update_books_filter()

    @property
    def callbacks(self):
        return {
            InsertBookTab.KEYS.FILE_INPUT: self.load_file_input,
            InsertBookTab.KEYS.CONFIRM: self.confirm,
            InsertBookTab.KEYS.UPDATE_FILTER: self.update_books_filter,
            InsertBookTab.KEYS.BOOKS_TABLE: self.select_book,
            InsertBookTab.KEYS.OPEN_BOOK: self.open_book_file
        }

    def handle_event(self, event):
        if str(event).startswith("KEYS.UPDATE_FILTER"):
            event = InsertBookTab.KEYS.UPDATE_FILTER

        super().handle_event(event)

    @staticmethod
    def parse_book_file(file):
        name_match = author_match = None
        for line in file:
            if not name_match:
                name_match = re.search(InsertBookTab.TITLE_REGEX, line)
            if not author_match:
                author_match = re.search(InsertBookTab.AUTHOR_REGEX, line)
            if name_match and author_match:
                break

        size = file.seek(0, 2)
        name = name_match.group(1) if name_match else None
        author = author_match.group(1) if author_match else None
        return size, name, author

    def load_file_input(self):
        path = self.file_input.get()
        book_name = splitext(split(path)[-1])[0].replace('_', ' ').title()

        try:
            with open(path, "r") as input_file:
                size, name, author = InsertBookTab.parse_book_file(input_file)
            size_str = f'{size} bytes'
            if name:
                book_name = name
            if not author:
                author = "Unknown"
        except (OSError, FileNotFoundError):
            size_str = "None"
            author = ""

        self.title_input.Update(book_name)
        self.author_input.Update(author)
        self.file_size_text.Update(f"File size: {size_str}")
        self.response_text.Update("")

    def confirm(self):
        error_msg = ""
        try:
            self.db.insert_book_to_db(self.title_input.get(),
                                      self.author_input.get(),
                                      self.file_input.get())
            self.update_books_table()

            self.file_input.Update("")
            self.title_input.Update("")
            self.author_input.Update("")
            self.file_size_text.Update("File size: None")
        except FileNotFoundError:
            error_msg = "Failed to open the file."
        except NonUniqueError:
            error_msg = "Book already exists."
        except CheckError:
            error_msg = "Illegal input."

        self.response_text.Update(error_msg)

    def update_books_filter(self):
        for filter_name, element in self.str_filters:
            letters_filter = element.get()
            if letters_filter:
                letters_filter = letters_filter.replace("\"", "\"\"")  # Escape all '"'
                letters_filter = letters_filter.replace("\\", "\\\\")  # Escape all '\'
                letters_filter = letters_filter.replace("%", "\\%")  # Escape all '%'
                letters_filter = letters_filter.replace("_", "\\_")  # Escape all '_'
                self.filters[filter_name] = f"%{letters_filter}%"
            else:
                self.filters[filter_name] = None

        self.update_books_table()

    def get_books_filter_tables(self):
        filter_tables = []
        if self.filters["name"]:
            filter_tables += ["word", "word_appearance"]
        return filter_tables

    def update_books_table(self):
        # books = self.db.new_cursor().execute("SELECT book_id, title, author, file_path FROM book").fetchall()
        books = self.db.search_books(tables=self.get_books_filter_tables(), **self.filters)
        self.books_table.Update(values=books)

    def select_book(self):
        if self.books_table.SelectedRows:
            selected_book_row = self.books_table.SelectedRows[0]
            if selected_book_row < len(self.books_table.Values):
                self.selected_book_id = self.books_table.Values[selected_book_row][0]

    def open_book_file(self):
        if self.books_table.SelectedRows:
            selected_book_row = self.books_table.SelectedRows[0]
            if selected_book_row < len(self.books_table.Values):
                selected_book_path = self.books_table.Values[selected_book_row][3]
                Popen(f'"{selected_book_path}"', shell=True)
