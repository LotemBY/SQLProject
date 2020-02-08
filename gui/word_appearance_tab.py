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

        self.select_books_dropdown = sg.Combo(values=["All"],
                                              default_value=" ",
                                              size=(20, 1),
                                              enable_events=True,
                                              readonly=True,
                                              text_color="dark red",
                                              font=(None, 12),
                                              background_color="#",  # Thats an invalid color, so no background is used
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
        self.context_window = sg.Multiline("", pad=(0, 5), size=(80, 20), disabled=True)

        word_selection_col = sg.Column(layout=[[self.select_word_list]])
        word_preview_col = sg.Column(layout=[[self.word_appr_table], [self.book_title], [self.context_window]],
                                     element_justification=sg.TEXT_LOCATION_CENTER)

        self.Layout([
            [filter_frame],
            [word_selection_col, word_preview_col]
        ])

        self.book_list = None
        self.book_names_to_id = None
        self.book_id_to_name = None
        self.selected_book_id = None
        self.curr_showed_book = None
        self.selected_word_id = None
        self.selected_word_length = None
        self.word_appr_list = None

    def start(self):
        text_widget = self.context_window.TKText  # type: ScrolledText
        text_widget.mark_set("highlightStart", "0.0")
        text_widget.mark_set("highlightEnd", "0.0")
        self.select_book()

    @property
    def callbacks(self):
        return {
            WordAppearanceTab.KEYS.BOOK_SELECTION: self.select_book,
            WordAppearanceTab.KEYS.WORDS_LIST: self.select_word,
            WordAppearanceTab.KEYS.APPR_TABLE: self.select_word_appr
        }

    def update_book_dropdown(self):
        book_list = self.db.new_cursor().execute("SELECT book_id, title || ' by ' || author FROM book").fetchall()
        self.book_names_to_id = {book_name: book_id for book_id, book_name in book_list}
        self.book_id_to_name = dict(reversed(item) for item in self.book_names_to_id.items())
        book_options = ["All"] + list(self.book_names_to_id.keys())
        self.select_books_dropdown.Update(values=book_options)
        self.update_words_list()

    def select_book(self):
        selected_book = self.select_books_dropdown.get()
        self.selected_book_id = self.book_names_to_id.get(selected_book, None)
        self.update_words_list()

    def update_words_list(self):
        self.words_list = self.db.search_word_appearances(cols=["word_id", "length", "name", "COUNT(word_index)"],
                                                          tables=["word"],
                                                          book_id=self.selected_book_id,
                                                          unique_words=True,
                                                          order_by="COUNT(word_index) desc").fetchall()
        print("Words list updated! " + str(len(self.words_list)))
        self.select_word_list.update(values=[f'{word[2]} ({word[3]})' for word in self.words_list])
        self.select_word()

    def select_word(self):
        select_word_list_indexes = self.select_word_list.GetIndexes()
        if select_word_list_indexes:
            selected_word_row = select_word_list_indexes[0]
            if selected_word_row < len(self.words_list):
                self.selected_word_id = self.words_list[selected_word_row][0]
                self.selected_word_length = self.words_list[selected_word_row][1]
                self.update_word_appr_table()

    def update_word_appr_table(self):
        appearances = self.db.search_word_appearances(
            cols=["book_id", "line_offset", "paragraph", "line", "line_index", "sentence", "sentence_index"],
            tables=["book"],
            book_id=self.selected_book_id,
            word_id=self.selected_word_id).fetchall()

        self.word_appr_table.Update(
            values=[[self.book_id_to_name[appr[0]]] + list(appr) for appr in appearances]
        )
        self.select_word_appr()
        self.hide_book_preview()

    def hide_book_preview(self):
        self.book_title.Update(value="")
        self.context_window.Update(value="")
        self.curr_showed_book = None

    def preview_book(self, book_id, book_name):
        if self.curr_showed_book != book_id:
            self.book_title.Update(value=book_name)
            path = self.db.cursor.execute("SELECT file_path FROM book WHERE book_id == ?", (book_id,)).fetchone()

            if not path:
                raise FileNotFoundError

            book_data = cached_read(path[0])
            self.context_window.Update(value=book_data)
            self.curr_showed_book = book_id

    def select_word_appr(self):
        if self.word_appr_table.SelectedRows:
            selected_word_appr_row = self.word_appr_table.SelectedRows[0]
            if selected_word_appr_row < len(self.word_appr_table.Values):
                if self.word_appr_table.Values[selected_word_appr_row]:
                    (appr_book_name, appr_book_id, appr_line_offset, _appr_paragraph, appr_line) = \
                        self.word_appr_table.Values[selected_word_appr_row][0:5]

                    try:
                        self.preview_book(appr_book_id, appr_book_name)
                    except FileNotFoundError:
                        return

                    text_widget = self.context_window.TKText  # type: ScrolledText
                    text_widget.tag_configure("highlight", foreground="brown", background="yellow")

                    start = "%d.%d" % (appr_line, appr_line_offset)
                    end = "%d.%d" % (appr_line, appr_line_offset + self.selected_word_length)
                    text_widget.tag_remove("highlight", "highlightStart", "highlightEnd")
                    text_widget.mark_set("highlightStart", start)
                    text_widget.mark_set("highlightEnd", end)
                    text_widget.tag_add("highlight", "highlightStart", "highlightEnd")
                    text_widget.see("highlightStart")
