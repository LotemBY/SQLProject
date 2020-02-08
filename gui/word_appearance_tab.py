from enum import Enum, auto
from tkinter.scrolledtext import ScrolledText

import PySimpleGUI as sg

from db_manager import BookDatabase
from gui.custom_tab import CustomTab
from utils.utils import cached_read


class WordAppearanceTab(CustomTab):
    class KEYS(Enum):
        BOOK_SELECTION = auto()
        WORDS_LIST = auto()
        APPR_TABLE = auto()

    def __init__(self, db: BookDatabase):
        super().__init__("View Words", [[]])
        self.db = db
        self.db.add_book_insert_callback(self.update_book_dropdown)

        self.book_list = []
        self.book_names = {}
        self.selected_book_id = '%'

        self.select_books_dropdown = sg.Combo(values=["All"],
                                              default_value=" ",
                                              size=(20, 1),
                                              enable_events=True,
                                              readonly=True,
                                              key=WordAppearanceTab.KEYS.BOOK_SELECTION)

        filter_layout = [[sg.Text("Book: "), self.select_books_dropdown], [sg.Text(size=(100, 0))]]
        filter_frame = sg.Frame("Filter", filter_layout, size=(10, 100), pad=(0, 20), title_location="n",
                                element_justification=sg.TEXT_LOCATION_CENTER)

        self.words_list = []
        self.select_word_list = sg.Listbox(values=[""],
                                           auto_size_text=True,
                                           size=(18, 100),
                                           select_mode=sg.SELECT_MODE_SINGLE,
                                           enable_events=True,
                                           key=WordAppearanceTab.KEYS.WORDS_LIST)
        self.selected_word_id = None

        self.word_appr_list = []
        headers = ["Book", "Book Id", "Offset", "Paragraph", "Line", "Line Index", "Sentence", "Sentence Index"]
        col_widths = [max(len(col), 6) for col in headers]
        col_widths[0] = 15
        self.word_appr_table = sg.Table(values=[[''] * len(headers)],
                                        headings=headers,
                                        num_rows=10,
                                        justification=sg.TEXT_LOCATION_CENTER,
                                        col_widths=col_widths,
                                        auto_size_columns=False,
                                        enable_events=True,
                                        visible_column_map=[True, False, False] + [True] * (len(headers) - 3),
                                        key=WordAppearanceTab.KEYS.APPR_TABLE)

        self.book_title = sg.Text("", font=(None, 15), justification=sg.TEXT_LOCATION_CENTER, auto_size_text=False)
        self.book_data = None
        self.context_window = sg.Multiline("", pad=(0, 5), size=(80, 20), disabled=True)

        word_selection_col = sg.Column(layout=[[self.select_word_list]])
        word_preview_col = sg.Column(layout=[[self.word_appr_table], [self.book_title], [self.context_window]],
                                     element_justification=sg.TEXT_LOCATION_CENTER)

        self.Layout([
            [filter_frame],
            [word_selection_col, word_preview_col]
        ])

    @property
    def callbacks(self):
        return {
            WordAppearanceTab.KEYS.BOOK_SELECTION: self.select_book,
            WordAppearanceTab.KEYS.WORDS_LIST: self.select_word,
            WordAppearanceTab.KEYS.APPR_TABLE: self.select_word_appr
        }

    def update_book_dropdown(self):
        self.book_list = self.db.new_cursor().execute("SELECT book_id, title, author FROM book").fetchall()
        self.book_names = {book_id: f'{title} by {author}' for book_id, title, author in self.book_list}
        book_options = ["All"] + list(self.book_names.values())
        self.select_books_dropdown.Update(values=book_options)

    def select_book(self):
        selected_book_index = self.select_books_dropdown.TKCombo.current()
        self.selected_book_id = self.book_list[selected_book_index - 1][0] if selected_book_index > 0 else '%'
        print(self.selected_book_id)
        self.update_words_list()

    def update_words_list(self):
        self.words_list = self.db.query_words_in_book(self.selected_book_id).fetchall()
        self.select_word_list.update(values=[word[1] for word in self.words_list])
        self.word_appr_table.Update(values=[''])

    def select_word(self):
        select_word_list_indexes = self.select_word_list.GetIndexes()
        if select_word_list_indexes:
            selected_word_row = select_word_list_indexes[0]
            if selected_word_row < len(self.words_list):
                self.selected_word_id = self.words_list[selected_word_row][0]
                apprs = self.db.query_words_appearance_in_book(self.selected_book_id, self.selected_word_id).fetchall()
                self.word_appr_table.Update(
                    values=[[self.book_names[appr[0]]] + list(appr) for appr in apprs]
                )

    def select_word_appr(self):
        if self.word_appr_table.SelectedRows:
            selected_word_appr_row = self.word_appr_table.SelectedRows[0]
            if selected_word_appr_row < len(self.word_appr_table.Values):
                if self.word_appr_table.Values[selected_word_appr_row]:
                    (selected_word_appr_book_name,
                     selected_word_appr_book_id,
                     selected_word_appr_line_offset,
                     _paragraph,
                     selected_word_appr_line) = self.word_appr_table.Values[selected_word_appr_row][0:5]

                    self.book_title.Update(value=selected_word_appr_book_name)

                    self.db.cursor.execute("SELECT file_path FROM book WHERE book_id == ?",
                                           (selected_word_appr_book_id,))

                    filename = self.db.cursor.fetchone()
                    if filename:
                        self.db.cursor.execute("SELECT length FROM word WHERE word_id == ?", (self.selected_word_id,))
                        word_length = self.db.cursor.fetchone()[0]
                        book_data = cached_read(filename[0])
                        self.context_window.Update(value=book_data)

                        text_widget = self.context_window.TKText  # type: ScrolledText
                        text_widget.tag_configure("highlight", foreground="brown", background="yellow")

                        start = "%d.%d" % (selected_word_appr_line, selected_word_appr_line_offset)
                        end = "%d.%d" % (selected_word_appr_line, selected_word_appr_line_offset + word_length)
                        text_widget.mark_set("highlightStart", start)
                        text_widget.mark_set("highlightEnd", end)
                        text_widget.tag_add("highlight", "highlightStart", "highlightEnd")
                        text_widget.see("highlightStart")
