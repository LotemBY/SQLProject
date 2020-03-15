from enum import Enum, auto

import PySimpleGUI as sg

import gui.simple_gui_helper as sgh
from db.exceptions import CheckError
from gui.book_context_manager import BookContextManager
from gui.tabs.custom_tab import CustomTab


class PhraseTab(CustomTab):
    class KEYS(Enum):
        PHRASE_INPUT = auto()
        ADD_PHRASE = auto()
        PHRASE_SELECTION = auto()
        PHRASE_APPR_TABLE = auto()

    def __init__(self, db):
        super().__init__(db, "Search Phrases", [[]])
        self.db.add_book_insert_callback(self.search_phrase)

        self.phrases = dict(self.db.all_phrases())
        self.selected_phrase_id = None
        self.curr_showed_book = None

        self.layout(
            [
                [sg.Sizer(v_pixels=20)],
                [sg.Sizer(h_pixels=12), self._create_phrase_insertion_column()],
                [sg.Sizer(v_pixels=20)],
                [sg.Sizer(h_pixels=12), self._create_phrase_preview_column()]
            ]
        )

    def _create_phrase_insertion_column(self):
        enter_phrase_txt = sg.Text(
            text="Insert a phrase:",
            size=(20, 1),
            font=sgh.BIG_FONT_SIZE
        )

        self.phrase_input = sg.InputText(
            default_text="",
            size=(41, 1),
            font=sgh.BIG_FONT_SIZE,
            text_color=sgh.INPUT_COLOR,
            enable_events=True,
            key=PhraseTab.KEYS.PHRASE_INPUT
        )
        add_phrase_button = sg.Ok("Insert", pad=(20, 1), size=(10, 1), key=PhraseTab.KEYS.ADD_PHRASE)

        search_phrase_txt = sg.Text(
            text="Phrase to be searched:",
            size=(20, 1),
            font=sgh.BIG_FONT_SIZE
        )

        self.phrase_dropdown = sg.Combo(
            values=[],
            default_value="",
            readonly=True,
            size=(40, 1),
            font=sgh.BIG_FONT_SIZE,
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            background_color=sgh.NO_BG,
            enable_events=True,
            key=PhraseTab.KEYS.PHRASE_SELECTION
        )

        self.phrase_input_error = sg.Text(
            text="",
            font=sgh.BIG_FONT_SIZE,
            text_color=sgh.ERROR_TEXT_COLOR,
            auto_size_text=False
        )

        col = sg.Column(
            layout=[
                [enter_phrase_txt, self.phrase_input, add_phrase_button, self.phrase_input_error],
                [search_phrase_txt, self.phrase_dropdown]
            ]
        )

        return col

    def _create_phrase_preview_column(self):
        self.appearances_count_text = sg.Text(
            text="Number of Appearances: None",
            font=sgh.BIG_FONT_SIZE,
            justification=sg.TEXT_LOCATION_CENTER,
            auto_size_text=False,
        )

        # header_name, is_visible
        headers = [
            ("Book Id", False),
            ("Book", True),
            ("Sentence", True),
            ("Start Sentence Index", True),
            ("Start Line", False),
            ("Start Line Offset", False),
            ("End Sentence Index", True),
            ("End Line", False),
            ("End Line Offset", False)
        ]
        col_widths = [max(len(col_name), 20) for col_name, _is_visible in headers]
        col_widths[1] = 50
        self.phrase_appr_table = sg.Table(
            values=[[''] * len(headers)],
            headings=[col_name for col_name, _is_visible in headers],
            num_rows=10,
            justification=sg.TEXT_LOCATION_CENTER,
            col_widths=col_widths,
            auto_size_columns=False,
            enable_events=True,
            select_mode=sg.SELECT_MODE_BROWSE,
            visible_column_map=[is_visible for _col_name, is_visible in headers],
            key=PhraseTab.KEYS.PHRASE_APPR_TABLE
        )

        book_title = sg.Text(
            text="",
            font=sgh.TITLE_FONT_SIZE,
            justification=sg.TEXT_LOCATION_CENTER,
            auto_size_text=False,
        )

        book_context_multiline = sg.Multiline(
            default_text="",
            size=(110, 25),
            text_color=sgh.MULTILINE_TEXT_COLOR,
            background_color=sgh.MULTILINE_BG_COLOR,
            disabled=True
        )

        self.context_manager = BookContextManager(self.db, book_context_multiline, book_title)

        col = sg.Column(
            layout=[
                [self.appearances_count_text],
                [self.phrase_appr_table],
                [book_title],
                [book_context_multiline]
            ],
            element_justification=sgh.CENTER
        )

        return col

    def initialize(self):
        self.context_manager.initialize()

    def reload_from_db(self):
        self.phrases = dict(self.db.all_phrases())
        self.update_phrase_dropdown()

    @property
    def callbacks(self):
        return {
            PhraseTab.KEYS.PHRASE_INPUT: self.clear_phrase_error,
            PhraseTab.KEYS.ADD_PHRASE: self.add_phrase,
            PhraseTab.KEYS.PHRASE_SELECTION: self.search_phrase,
            PhraseTab.KEYS.PHRASE_APPR_TABLE: self.select_phrase_appr
        }

    def handle_enter(self, focused_element):
        if focused_element == self.phrase_input:
            self.add_phrase()

    def clear_phrase_error(self):
        self.phrase_input_error.update("")

    def add_phrase(self):
        phrase = self.phrase_input.get()
        if phrase not in self.phrases:
            try:
                self.phrases[phrase] = self.db.create_phrase(phrase)
                self.phrase_input.update("")
                self.update_phrase_dropdown(curr_value=phrase)
            except CheckError:
                self.phrase_input_error.update("Illegal phrase.", text_color=sgh.ERROR_TEXT_COLOR)
        else:
            self.phrase_input_error.update("Phrase already inserted.", text_color=sgh.ERROR_TEXT_COLOR)

    def update_phrase_dropdown(self, curr_value=""):
        self.phrase_dropdown.update(values=list(self.phrases.keys()), value=curr_value)
        self.search_phrase()

    def search_phrase(self):
        selected_phrase = self.phrase_dropdown.get()
        self.selected_phrase_id = self.phrases.get(selected_phrase)
        self.update_phrase_appr_table()

    def update_phrase_appr_table(self):
        if self.selected_phrase_id:
            appearances = self.db.find_phrase(self.selected_phrase_id)

            phrases_appr_table_values = []
            for book_id, sentence, start_index, end_index in appearances:
                start_line, start_line_offset = self.db.word_location_to_offset(book_id, sentence, start_index)
                end_line, end_line_offset = self.db.word_location_to_offset(book_id, sentence, end_index, True)

                phrases_appr_table_values.append((book_id, self.db.get_book_title(book_id)[0],
                                                  sentence,
                                                  start_index, start_line, start_line_offset,
                                                  end_index, end_line, end_line_offset))

            self.appearances_count_text.update(value=f"Number of Appearances: {len(phrases_appr_table_values)}")
            self.phrase_appr_table.update(values=phrases_appr_table_values)
        else:
            self.appearances_count_text.update(value=f"Number of Appearances: None")
            self.phrase_appr_table.update(values=[])

        if self.phrase_appr_table.TKTreeview.get_children():
            # Manually select the first appearance to be shown
            self.phrase_appr_table.TKTreeview.selection_set(1)  # This updates the GUI widget
            self.phrase_appr_table.SelectedRows = [0]  # This updates PySimpleGUI's rows logic
            self.select_phrase_appr()
        else:
            self.context_manager.hide_context()

    def select_phrase_appr(self):
        if self.phrase_appr_table.SelectedRows:
            selected_word_appr_row = self.phrase_appr_table.SelectedRows[0]
            if selected_word_appr_row < len(self.phrase_appr_table.Values):
                if self.phrase_appr_table.Values[selected_word_appr_row]:
                    (book_id, book_title,
                     sentence,
                     start_index, start_line, start_line_offset,
                     end_index, end_line, end_line_offset) = self.phrase_appr_table.Values[selected_word_appr_row]

                    self.context_manager.set_context(book_id, start_line, start_line_offset, end_line, end_line_offset)


