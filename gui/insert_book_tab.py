import os
import re
from enum import Enum, auto
from os.path import splitext, split

import PySimpleGUI as sg

import book_parser
from gui.custom_tab import CustomTab


class InsertBookTab(CustomTab):
    AUTHOR_REGEX = r"Author: (.+)$"
    TITLE_REGEX = r"Title: (.+)$"

    class KEYS(Enum):
        FILE_INPUT = auto()
        CONFIRM = auto()
        BOOKS_TABLE = auto()
        OPEN_BOOK = auto()

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

    def __init__(self, db):
        super().__init__("Insert Book", [[]])
        self.db = db
        self.db.add_book_insert_callback(self.update_books_table)

        self.file_input = sg.InputText(enable_events=True, key=InsertBookTab.KEYS.FILE_INPUT)
        self.browse_button = sg.FileBrowse(file_types=(("Text files", "*.txt"), ("All Files", "*")))
        self.title_input = sg.InputText()
        self.author_input = sg.InputText()

        self.file_size_text = sg.Text("File size: None", auto_size_text=False)
        self.response_text = sg.Text("", text_color="red", auto_size_text=False)

        self.books_table = sg.Table(values=[[''] * 4],
                                    headings=["Book ID", "Title", "Author", "Path"],
                                    num_rows=10,
                                    justification=sg.TEXT_LOCATION_LEFT,
                                    col_widths=[0, 15, 15, 35],
                                    auto_size_columns=False,
                                    enable_events=True,
                                    visible_column_map=[False, True, True, True],
                                    key=InsertBookTab.KEYS.BOOKS_TABLE)
        self.selected_book_id = None

        insert_book_button = sg.Ok("Insert Book", key=InsertBookTab.KEYS.CONFIRM, size=(20, 0))
        open_book_button = sg.Button("Open Selected Book", key=InsertBookTab.KEYS.OPEN_BOOK)

        books_frame = sg.Frame("Books",
                               [
                                   [self.books_table],
                                   [sg.Text("", size=(60, 0)), open_book_button]
                               ],
                               element_justification=sg.TEXT_LOCATION_CENTER, pad=(10, 10))

        self.Layout([
            [sg.Text("Path:", size=(5, 0)), self.file_input, self.browse_button],
            [sg.Text("Title:", size=(5, 0)), self.title_input],
            [sg.Text("Author:", size=(5, 0)), self.author_input],
            [self.file_size_text],
            [insert_book_button, self.response_text],
            [books_frame]
        ])

    @property
    def callbacks(self):
        return {
            InsertBookTab.KEYS.FILE_INPUT: self.load_file_input,
            InsertBookTab.KEYS.CONFIRM: self.confirm,
            InsertBookTab.KEYS.BOOKS_TABLE: self.select_book,
            InsertBookTab.KEYS.OPEN_BOOK: self.open_book_file
        }

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
        try:
            if book_parser.insert_book_to_db(self.db,
                                             self.title_input.get(),
                                             self.author_input.get(),
                                             self.file_input.get()):
                self.update_books_table()
                self.file_input.Update("")
                self.title_input.Update("")
                self.author_input.Update("")
                self.file_size_text.Update("File size: None")
            else:
                self.response_text.Update("Book already exists.")
        except FileNotFoundError:
            self.response_text.Update("Failed to open the file.")

    def update_books_table(self):
        self.books_table.Update(values=self.db.new_cursor().execute("SELECT book_id, title, author, file_path FROM book").fetchall())

    def open_book_file(self):
        if self.books_table.SelectedRows:
            selected_book_row = self.books_table.SelectedRows[0]
            if selected_book_row < len(self.books_table.Values):
                selected_book_path = self.books_table.Values[selected_book_row][3]
                os.system(f'"{selected_book_path}" &')

    def select_book(self):
        if self.books_table.SelectedRows:
            selected_book_row = self.books_table.SelectedRows[0]
            if selected_book_row < len(self.books_table.Values):
                self.selected_book_id = self.books_table.Values[selected_book_row][0]
