from enum import Enum, auto
from threading import Timer
from tkinter.scrolledtext import ScrolledText

import PySimpleGUI as sg

import gui.simple_gui_helper as sgh
from gui.custom_tab import CustomTab
from utils.utils import cached_read


class WordAppearanceTab(CustomTab):
    WORDS_SORT_OPTIONS = {
        "Alphabet": "name",
        "Appearances": "COUNT(word_index)",
        "Length": "length"
    }

    WORDS_SORT_DIRECTION = {
        "Increasing": "asc",
        "Decreasing": "desc",
    }

    DEFAULT_WORDS_SORT_ORDER = "Appearances"
    DEFAULT_WORDS_SORT_DIRECTION = "Decreasing"

    REGEX_HELP_TEXT = "You can use this filter to search for specific words.\n" \
                      "\n" \
                      "Use  _  as a wildcard for any character.\n" \
                      "Use  *   as a wildcard for 0 or more characters."

    class KEYS(Enum):
        UPDATE_FILTER = auto()
        SCHEDULE_UPDATE_FILTER = auto()
        REGEX_HELP = auto()
        WORDS_SORT = auto()
        WORDS_DIRECTION = auto()
        WORDS_LIST = auto()
        APPR_TABLE = auto()

    def __init__(self, db):
        super().__init__(db, "View Words", [[]])
        self.db.add_book_insert_callback(self.update_book_dropdown)
        self.db.add_group_insert_callback(self.update_group_dropdown)
        self.db.add_group_word_insert_callback(self.group_word_insertion_callback)
        sg.SetOptions(input_text_color=sgh.get_theme_field("TEXT_INPUT"))

        self.curr_words_order = \
            WordAppearanceTab.WORDS_SORT_OPTIONS[WordAppearanceTab.DEFAULT_WORDS_SORT_ORDER]
        self.curr_words_direction = \
            WordAppearanceTab.WORDS_SORT_DIRECTION[WordAppearanceTab.DEFAULT_WORDS_SORT_DIRECTION]

        self.update_filter_timer = None
        self.old_word_appearance_filters = None

        self.words_list = []
        self.book_names_to_id = {}
        self.book_id_to_title_and_full_name = {}
        self.group_name_to_id = {"All": "%"}
        self.curr_showed_book = None
        self.selected_word_id = None
        self.selected_word_length = None
        self.words_filters = {}
        self.word_appearance_filters = {}

        self.Layout([
            [self._create_filter_frame()],
            [self._create_word_list_column(), self._create_word_preview_column()]
        ])

    def _create_filter_frame(self):
        self.book_filter_dropdown = sg.Combo(
            values=["All"],
            default_value="All",
            size=(20, 1),
            enable_events=True,
            readonly=True,
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            font=(None, 12),
            background_color=sgh.NO_BG,
            key=WordAppearanceTab.KEYS.UPDATE_FILTER
        )

        self.group_filter_dropdown = sg.Combo(
            values=["None", "All"],
            default_value="None",
            size=(20, 1),
            enable_events=True,
            readonly=True,
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            font=(None, 12),
            background_color=sgh.NO_BG,
            key=WordAppearanceTab.KEYS.UPDATE_FILTER
        )

        self.letters_filter_input = sg.InputText(
            default_text="",
            size=(21, 1),
            enable_events=True,
            text_color=sgh.INPUT_COLOR,
            key=WordAppearanceTab.KEYS.SCHEDULE_UPDATE_FILTER
        )

        info_button = sg.Help("?", size=(2, 1), key=WordAppearanceTab.KEYS.REGEX_HELP)

        def _create_int_input():
            return sg.InputText(
                default_text="",
                size=(10, 1),
                enable_events=True,
                background_color=sgh.THEME["INPUT"],
                text_color=sgh.INPUT_COLOR,
                key=WordAppearanceTab.KEYS.SCHEDULE_UPDATE_FILTER
            )

        line_filter = _create_int_input()
        line_index_filer = _create_int_input()
        sentence_filter = _create_int_input()
        sentence_index_filter = _create_int_input()
        paragraph_filter = _create_int_input()

        self.int_filters = (
            (line_filter, "line"),
            (line_index_filer, "line_index"),
            (sentence_index_filter, "sentence_index"),
            (sentence_filter, "sentence"),
            (paragraph_filter, "paragraph")
        )

        col1 = sg.Column(
            layout=[
                [sg.Text("Word: ", pad=(0, 5), size=(10, 1)), self.letters_filter_input, info_button],
                [sg.Text("Book: ", pad=(0, 5), size=(10, 1)), self.book_filter_dropdown],
                [sg.Text("Group: ", pad=(0, 5), size=(10, 1)), self.group_filter_dropdown]
            ]
        )

        col2 = sg.Column(
            layout=[
                [sg.Text("Line: ", pad=(0, 5), size=(10, 1)), line_filter],
                [sg.Text("Sentence: ", pad=(0, 5), size=(10, 1)), sentence_filter],
                [sg.Text("Paragraph: ", pad=(0, 5), size=(10, 1)), paragraph_filter]
            ]
        )

        col3 = sg.Column(
            layout=[
                [sg.Text("Line Index: ", pad=(20, 5), size=(12, 1)), line_index_filer],
                [sg.Text("Sentence Index: ", pad=(20, 5), size=(12, 1)), sentence_index_filter],
            ]
        )

        # TODO: Clear filter button

        frame = sg.Frame(
            title="Words Filter",
            layout=[
                [col1, col2, col3],
                [sg.Sizer(h_pixels=10000)]
            ],
            size=(10, 100),
            pad=(0, (0, 10)),
            title_location=sg.TITLE_LOCATION_TOP,
            element_justification=sgh.CENTER)

        return frame

    def _create_word_list_column(self):
        self.words_order_dropdown = sg.Combo(
            values=list(WordAppearanceTab.WORDS_SORT_OPTIONS.keys()),
            default_value=WordAppearanceTab.DEFAULT_WORDS_SORT_ORDER,
            size=(11, 1),
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            enable_events=True,
            readonly=True,
            background_color=sgh.NO_BG,
            key=WordAppearanceTab.KEYS.WORDS_SORT
        )

        self.words_direction_dropdown = sg.Combo(
            values=list(WordAppearanceTab.WORDS_SORT_DIRECTION.keys()),
            default_value=WordAppearanceTab.DEFAULT_WORDS_SORT_DIRECTION,
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            size=(11, 1),
            enable_events=True,
            readonly=True,
            background_color=sgh.NO_BG,
            key=WordAppearanceTab.KEYS.WORDS_DIRECTION
        )

        self.select_word_list = sg.Listbox(
            values=[""],
            auto_size_text=True,
            size=(20, 100),
            select_mode=sg.SELECT_MODE_SINGLE,
            enable_events=True,
            key=WordAppearanceTab.KEYS.WORDS_LIST
        )

        col = sg.Column(
            layout=[
                [sg.Text("Sort by: ", size=(6, 1)), self.words_order_dropdown],
                [sg.Text("Order: ", size=(6, 1)), self.words_direction_dropdown],
                [self.select_word_list]
            ]
        )

        return col

    def _create_word_preview_column(self):
        headers = ["Book", "Book Id", "Offset", "Paragraph", "Line", "Line Index", "Sentence", "Sentence Index"]
        col_widths = [max(len(col), 4) for col in headers]
        col_widths[0] = 15
        self.word_appr_table = sg.Table(
            values=[[''] * len(headers)],
            headings=headers,
            num_rows=10,
            justification=sg.TEXT_LOCATION_CENTER,
            col_widths=col_widths,
            auto_size_columns=False,
            enable_events=True,
            select_mode=sg.SELECT_MODE_BROWSE,
            visible_column_map=[True, False, False] + [True] * (len(headers) - 3),
            key=WordAppearanceTab.KEYS.APPR_TABLE
        )

        self.book_title = sg.Text(
            text="",
            font=(None, 15),
            justification=sg.TEXT_LOCATION_CENTER,
            auto_size_text=False
        )
        self.context_window = sg.Multiline(
            default_text="",
            size=(80, 25),
            text_color=sgh.MULTILINE_TEXT_COLOR,
            background_color=sgh.MULTILINE_BG_COLOR,
            disabled=True
        )

        col = sg.Column(
            layout=[
                [self.word_appr_table],
                [self.book_title],
                [self.context_window]
            ],
            element_justification=sgh.CENTER
        )

        return col

    def initialize(self):
        text_widget = self.context_window.TKText  # type: ScrolledText
        text_widget.tag_configure("highlight",
                                  foreground=sgh.WORD_HIGHLIGHT_TEXT_COLOR,
                                  background=sgh.WORD_HIGHLIGHT_BG_COLOR)
        text_widget.mark_set("highlightStart", "0.0")
        text_widget.mark_set("highlightEnd", "0.0")
        self.update_filter()

    @property
    def callbacks(self):
        return {
            WordAppearanceTab.KEYS.UPDATE_FILTER: self.update_filter,
            WordAppearanceTab.KEYS.SCHEDULE_UPDATE_FILTER: self.schedule_filter_update,
            WordAppearanceTab.KEYS.REGEX_HELP: self.show_regex_help,
            WordAppearanceTab.KEYS.WORDS_SORT: self.update_words_sort_order,
            WordAppearanceTab.KEYS.WORDS_DIRECTION: self.update_words_sort_direction,
            WordAppearanceTab.KEYS.WORDS_LIST: self.select_word,
            WordAppearanceTab.KEYS.APPR_TABLE: self.select_word_appr
        }

    def handle_event(self, event):
        # TODO: this is ugly as fuck
        if str(event).startswith("KEYS.UPDATE_FILTER"):
            event = WordAppearanceTab.KEYS.UPDATE_FILTER
        if str(event).startswith("KEYS.SCHEDULE_UPDATE_FILTER"):
            event = WordAppearanceTab.KEYS.SCHEDULE_UPDATE_FILTER

        super().handle_event(event)

    @staticmethod
    def show_regex_help():
        sg.popup_ok(
            WordAppearanceTab.REGEX_HELP_TEXT,
            title="Words Search Syntax",
            font=(None, 13),
            non_blocking=False
        )

    def update_book_dropdown(self):
        books = self.db.all_books()
        self.book_id_to_title_and_full_name = \
            {book_id: (title, f'{title} by {author}') for book_id, title, author in books}
        self.book_names_to_id = \
            {f'{title} by {author}': book_id for book_id, title, author in books}

        book_options = ["All"] + list(self.book_names_to_id.keys())
        self.book_filter_dropdown.Update(values=book_options, value=self.book_filter_dropdown.get())

        # Update the words list if we filter for all books
        if self.word_appearance_filters["book_id"] is None:
            self.update_words_list()

    def update_group_dropdown(self):
        self.group_name_to_id["All"] = "%"
        groups_list = self.db.all_groups()
        self.group_name_to_id.update({name: group_id for group_id, name in groups_list})

        selected_option = self.group_filter_dropdown.get()
        group_options = ["None"] + list(self.group_name_to_id.keys())
        self.group_filter_dropdown.Update(values=group_options, value=selected_option)

        # If we selected "All" we need to update the list with words from the new group
        if selected_option == "All":
            self.update_words_list()

    def group_word_insertion_callback(self, group_id):
        # If the group filter contains the group_id, we need to update the words list
        if self.words_filters["group_id"] in (group_id, "%"):
            self.update_words_list()

    def cancel_filter_scheduler(self):
        if self.update_filter_timer is not None and self.update_filter_timer.is_alive():
            self.update_filter_timer.cancel()
            self.update_filter_timer = None

    def trigger_filter_update_event(self):
        window = self.ParentForm

        window.LastButtonClicked = WordAppearanceTab.KEYS.UPDATE_FILTER
        window.FormRemainedOpen = True
        if window.CurrentlyRunningMainloop:
            window.TKroot.quit()

    def schedule_filter_update(self):
        self.cancel_filter_scheduler()
        self.update_filter_timer = Timer(
            interval=0.5,
            function=self.trigger_filter_update_event
        )

        self.update_filter_timer.start()

        # We can already get the int filters, to immediately change the bg color if illegal input was inserted
        for element, filter_name in self.int_filters:
            self.word_appearance_filters[filter_name] = \
                WordAppearanceTab.get_int_input(element, self.words_filters.get(filter_name, None))

    def update_filter(self):
        self.cancel_filter_scheduler()
        old_words_filters = self.words_filters.copy()

        # Words appearance filters
        selected_group = self.group_filter_dropdown.get()
        self.words_filters["group_id"] = self.group_name_to_id.get(selected_group, None)

        letters_filter = self.letters_filter_input.get()
        letters_filter = letters_filter.replace("\"", "\"\"")  # Escape all '"'
        letters_filter = letters_filter.replace("\\", "\\\\")  # Escape all '\'
        letters_filter = letters_filter.replace("%", "\\%")  # Escape all '%'
        letters_filter = letters_filter.replace("*", "%")
        # letters_filter += "%"
        self.words_filters["name"] = letters_filter

        # Word appearance filters
        selected_book = self.book_filter_dropdown.get()
        self.word_appearance_filters["book_id"] = self.book_names_to_id.get(selected_book, None)

        if self.words_filters != old_words_filters or \
                self.word_appearance_filters != self.old_word_appearance_filters:
            self.update_words_list()
            self.old_word_appearance_filters = self.word_appearance_filters.copy()

    @staticmethod
    def get_int_input(input_element, default_value):
        int_input = default_value
        entered_number = input_element.get()
        try:
            int_input = int(entered_number)
            legal_number = True
        except ValueError:
            legal_number = len(entered_number) == 0
            if legal_number:
                int_input = None

        input_element.Update(background_color=
                             sgh.GOOD_INPUT_BG_COLOR if legal_number else sgh.BAD_INPUT_BG_COLOR)
        return int_input

    def update_words_sort_order(self):
        new_order = WordAppearanceTab.WORDS_SORT_OPTIONS.get(self.words_order_dropdown.get(), None)
        if new_order is not None:
            old_order = self.curr_words_order
            self.curr_words_order = new_order

            if self.curr_words_order != old_order:
                self.update_words_list()

    def update_words_sort_direction(self):
        new_dir = WordAppearanceTab.WORDS_SORT_DIRECTION.get(self.words_direction_dropdown.get(), None)
        if new_dir is not None:
            old_dir = self.curr_words_direction
            self.curr_words_direction = new_dir

            if self.curr_words_direction != old_dir:
                self.update_words_list()

    def get_words_filter_tables(self):
        filter_tables = []
        if self.words_filters["group_id"] is not None:
            filter_tables.append("word_in_group")
        return filter_tables

    def update_words_list(self):
        self.words_list = self.db.search_word_appearances(
            cols=["word_id", "length", "name", "COUNT(word_index)"],
            tables=set(["word"] + self.get_words_filter_tables()),
            unique_words=True,
            order_by=self.curr_words_order + " " + self.curr_words_direction,
            **self.words_filters,
            **self.word_appearance_filters)

        self.select_word_list.update(values=[f'{word[2]} ({word[3]})' for word in self.words_list])
        self.select_word()

    def select_word(self):
        select_word_list_indexes = self.select_word_list.GetIndexes()
        if select_word_list_indexes:
            selected_word_row = select_word_list_indexes[0]
            if selected_word_row < len(self.words_list):
                self.selected_word_id = self.words_list[selected_word_row][0]
                self.selected_word_length = self.words_list[selected_word_row][1]
        else:
            self.selected_word_id = None
            self.selected_word_length = None

        # Update the words list anyways, to show the new words \ hide the old ones
        self.update_word_appr_table()

    def update_word_appr_table(self):
        if self.selected_word_id:
            appearances = self.db.search_word_appearances(
                cols=["book_id", "line_offset", "paragraph", "line", "line_index", "sentence", "sentence_index"],
                tables=["book"],
                word_id=self.selected_word_id,
                **self.word_appearance_filters)

            self.word_appr_table.Update(
                values=[[self.book_id_to_title_and_full_name[appr[0]][0]] + list(appr) for appr in appearances]
            )
        else:
            self.word_appr_table.Update(values=[])

        if self.word_appr_table.TKTreeview.get_children():
            # Manually select the first appearance to be shown
            self.word_appr_table.TKTreeview.selection_set(1)  # This updates the GUI widget
            self.word_appr_table.SelectedRows = [0]  # This updates PySimpleGUI's rows logic
            self.select_word_appr()
        else:
            self.hide_book_preview()

    def hide_book_preview(self):
        self.book_title.Update(value="")
        self.context_window.Update(value="")
        self.curr_showed_book = None

    def preview_book(self, book_id):
        if self.curr_showed_book != book_id:
            self.book_title.Update(value=self.book_id_to_title_and_full_name[book_id][1])
            path = self.db.get_book_path(book_id)

            if not path:
                raise FileNotFoundError

            book_data = cached_read(path[0])
            self.context_window.Update(value=book_data)
            self.curr_showed_book = book_id

    def set_context_window_highlight(self, line, line_offset, length):
        text_widget = self.context_window.TKText  # type: ScrolledText
        start = "%d.%d" % (line, line_offset)
        end = "%d.%d" % (line, line_offset + length)
        text_widget.tag_remove("highlight", "highlightStart", "highlightEnd")
        text_widget.mark_set("highlightStart", start)
        text_widget.mark_set("highlightEnd", end)
        text_widget.tag_add("highlight", "highlightStart", "highlightEnd")
        text_widget.see("highlightStart")

    def select_word_appr(self):
        if self.word_appr_table.SelectedRows:
            selected_word_appr_row = self.word_appr_table.SelectedRows[0]
            if selected_word_appr_row < len(self.word_appr_table.Values):
                if self.word_appr_table.Values[selected_word_appr_row]:
                    (appr_book_name, appr_book_id, appr_line_offset, _appr_paragraph, appr_line) = \
                        self.word_appr_table.Values[selected_word_appr_row][0:5]

                    try:
                        self.preview_book(appr_book_id)
                    except FileNotFoundError:
                        return

                    self.set_context_window_highlight(appr_line, appr_line_offset, self.selected_word_length)

