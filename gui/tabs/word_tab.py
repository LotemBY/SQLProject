from enum import Enum, auto
from threading import Timer

import PySimpleGUI as sg

import gui.simple_gui_helper as sgh
from gui.book_context_manager import BookContextManager
from gui.tabs.custom_tab import CustomTab


class WordTab(CustomTab):
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
        sg.SetOptions(input_text_color=sgh.get_theme_field("TEXT_INPUT"))  # For the color of the words list

        self.curr_words_order = \
            WordTab.WORDS_SORT_OPTIONS[WordTab.DEFAULT_WORDS_SORT_ORDER]
        self.curr_words_direction = \
            WordTab.WORDS_SORT_DIRECTION[WordTab.DEFAULT_WORDS_SORT_DIRECTION]

        self.update_filter_timer = None
        self.old_word_appearance_filters = None

        self.words_list = []
        self.book_names_to_id = {}
        self.group_name_to_id = {"All": "%"}
        self.curr_showed_book = None
        self.selected_word_id = None
        self.selected_word_length = None
        self.words_filters = {}
        self.word_appearance_filters = {}

        self.layout([
            [self._create_filter_frame()],
            [self._create_word_list_column(), self._create_word_preview_column()]
        ])

    def _create_filter_frame(self):
        self.letters_filter_input = sg.InputText(
            default_text="",
            size=(30, 1),
            pad=(0, 1),
            enable_events=True,
            text_color=sgh.INPUT_COLOR,
            key=WordTab.KEYS.SCHEDULE_UPDATE_FILTER
        )

        self.book_filter_dropdown = sg.Combo(
            values=["All"],
            default_value="All",
            size=(35, 1),
            pad=(0, 1),
            enable_events=True,
            readonly=True,
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            font=sgh.SMALL_FONT_SIZE,
            background_color=sgh.NO_BG,
            key=WordTab.KEYS.UPDATE_FILTER
        )

        self.group_filter_dropdown = sg.Combo(
            values=["None", "All"],
            default_value="None",
            size=(35, 1),
            pad=(0, 1),
            enable_events=True,
            readonly=True,
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            font=sgh.SMALL_FONT_SIZE,
            background_color=sgh.NO_BG,
            key=WordTab.KEYS.UPDATE_FILTER
        )

        info_button = sg.Help("?", size=(3, 1), pad=(10, 1), key=WordTab.KEYS.REGEX_HELP)

        def _create_int_input():
            return sg.InputText(
                default_text="",
                size=(17, 1),
                pad=(0, 1),
                enable_events=True,
                background_color=sgh.THEME["INPUT"],
                text_color=sgh.INPUT_COLOR,
                key=WordTab.KEYS.SCHEDULE_UPDATE_FILTER
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
            values=list(WordTab.WORDS_SORT_OPTIONS.keys()),
            default_value=WordTab.DEFAULT_WORDS_SORT_ORDER,
            size=(11, 1),
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            enable_events=True,
            readonly=True,
            background_color=sgh.NO_BG,
            key=WordTab.KEYS.WORDS_SORT
        )

        self.words_direction_dropdown = sg.Combo(
            values=list(WordTab.WORDS_SORT_DIRECTION.keys()),
            default_value=WordTab.DEFAULT_WORDS_SORT_DIRECTION,
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            size=(11, 1),
            enable_events=True,
            readonly=True,
            background_color=sgh.NO_BG,
            key=WordTab.KEYS.WORDS_DIRECTION
        )

        self.words_counter_text = sg.Text("0 Results.", size=(11, 1), auto_size_text=False)

        self.select_word_list = sg.Listbox(
            values=[""],
            auto_size_text=True,
            size=(20, 100),
            select_mode=sg.SELECT_MODE_SINGLE,
            enable_events=True,
            key=WordTab.KEYS.WORDS_LIST
        )

        col = sg.Column(
            layout=[
                [sg.Text("Sort by: ", size=(6, 1)), self.words_order_dropdown],
                [sg.Text("Order: ", size=(6, 1)), self.words_direction_dropdown],
                [self.words_counter_text],
                [self.select_word_list]
            ]
        )

        return col

    def _create_word_preview_column(self):
        # header_name, is_visible
        headers = [
            ("Book", True),
            ("Book Id", False),
            ("Offset", False),
            ("Paragraph", True),
            ("Line", True),
            ("Line Index", True),
            ("Sentence", True),
            ("Sentence Index", True)
        ]

        col_widths = [max(len(col_name), 10) for col_name, _is_visible in headers]
        col_widths[0] = 30
        self.word_appr_table = sg.Table(
            values=[[''] * len(headers)],
            headings=[col_name for col_name, _is_visible in headers],
            num_rows=10,
            justification=sg.TEXT_LOCATION_CENTER,
            col_widths=col_widths,
            auto_size_columns=False,
            enable_events=True,
            select_mode=sg.SELECT_MODE_BROWSE,
            visible_column_map=[is_visible for _col_name, is_visible in headers],
            key=WordTab.KEYS.APPR_TABLE
        )

        book_title = sg.Text(
            text="",
            font=sgh.TITLE_FONT_SIZE,
            justification=sg.TEXT_LOCATION_CENTER,
            auto_size_text=False
        )
        book_context_multiline = sg.Multiline(
            default_text="",
            size=(100, 25),
            text_color=sgh.MULTILINE_TEXT_COLOR,
            background_color=sgh.MULTILINE_BG_COLOR,
            disabled=True
        )

        self.context_manager = BookContextManager(self.db, book_context_multiline, book_title)

        col = sg.Column(
            layout=[
                [self.word_appr_table],
                [book_title],
                [book_context_multiline]
            ],
            element_justification=sgh.CENTER
        )

        return col

    def initialize(self):
        self.context_manager.initialize()
        self.update_filter()

    def reload_from_db(self):
        self.update_book_dropdown()
        self.update_group_dropdown()
        self.book_filter_dropdown.update(value="All")
        self.group_filter_dropdown.update(value="None")
        self.update_filter()

    @property
    def callbacks(self):
        return {
            WordTab.KEYS.UPDATE_FILTER: self.update_filter,
            WordTab.KEYS.SCHEDULE_UPDATE_FILTER: self.schedule_filter_update,
            WordTab.KEYS.REGEX_HELP: self.show_regex_help,
            WordTab.KEYS.WORDS_SORT: self.update_words_sort_order,
            WordTab.KEYS.WORDS_DIRECTION: self.update_words_sort_direction,
            WordTab.KEYS.WORDS_LIST: self.select_word,
            WordTab.KEYS.APPR_TABLE: self.select_word_appr
        }

    def handle_event(self, event):
        # TODO: this is ugly as fuck
        if str(event).startswith("KEYS.UPDATE_FILTER"):
            event = WordTab.KEYS.UPDATE_FILTER
        if str(event).startswith("KEYS.SCHEDULE_UPDATE_FILTER"):
            event = WordTab.KEYS.SCHEDULE_UPDATE_FILTER

        super().handle_event(event)

    @staticmethod
    def show_regex_help():
        sg.popup_ok(
            WordTab.REGEX_HELP_TEXT,
            title="Words Search Syntax",
            font=sgh.FONT,
            non_blocking=False
        )

    def update_book_dropdown(self):
        books = self.db.all_books()
        self.book_names_to_id = {f'{title} by {author}': book_id for book_id, title, author, _path, _date in books}

        book_options = ["All"] + list(self.book_names_to_id.keys())
        self.book_filter_dropdown.update(values=book_options, value=self.book_filter_dropdown.get())

        # Update the words list if we filter for all books
        if self.word_appearance_filters["book_id"] is None:
            self.update_words_list()

    def update_group_dropdown(self):
        self.group_name_to_id = {"All": "%"}
        groups_list = self.db.all_groups()
        self.group_name_to_id.update({name: group_id for group_id, name in groups_list})

        selected_option = self.group_filter_dropdown.get()
        group_options = ["None"] + list(self.group_name_to_id.keys())
        self.group_filter_dropdown.update(values=group_options, value=selected_option)

        # If we selected "All" we need to update the list with words from the new group
        if selected_option == "All":
            self.update_words_list()

    def group_word_insertion_callback(self, group_id):
        import time
        time.sleep(10)
        # If the group filter contains the group_id, we need to update the words list
        if self.words_filters["group_id"] in (group_id, "%"):
            self.update_words_list()

    def cancel_filter_scheduler(self):
        if self.update_filter_timer is not None and self.update_filter_timer.is_alive():
            self.update_filter_timer.cancel()
            self.update_filter_timer = None

    def trigger_filter_update_event(self):
        window = self.ParentForm

        window.LastButtonClicked = WordTab.KEYS.UPDATE_FILTER
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
                WordTab.get_int_input(element, self.words_filters.get(filter_name))

    def update_filter(self):
        self.cancel_filter_scheduler()
        old_words_filters = self.words_filters.copy()

        # Words appearance filters
        selected_group = self.group_filter_dropdown.get()
        self.words_filters["group_id"] = self.group_name_to_id.get(selected_group)

        letters_filter = self.letters_filter_input.get()
        letters_filter = letters_filter.replace("\"", "\"\"")  # Escape all '"'
        letters_filter = letters_filter.replace("\\", "\\\\")  # Escape all '\'
        letters_filter = letters_filter.replace("%", "\\%")  # Escape all '%'
        letters_filter = letters_filter.replace("*", "%")
        # letters_filter += "%"
        self.words_filters["name"] = letters_filter

        # Word appearance filters
        selected_book = self.book_filter_dropdown.get()
        self.word_appearance_filters["book_id"] = self.book_names_to_id.get(selected_book)

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

        input_element.update(background_color=
                             sgh.GOOD_INPUT_BG_COLOR if legal_number else sgh.BAD_INPUT_BG_COLOR)
        return int_input

    def update_words_sort_order(self):
        new_order = WordTab.WORDS_SORT_OPTIONS.get(self.words_order_dropdown.get())
        if new_order is not None:
            old_order = self.curr_words_order
            self.curr_words_order = new_order

            if self.curr_words_order != old_order:
                self.update_words_list()

    def update_words_sort_direction(self):
        new_dir = WordTab.WORDS_SORT_DIRECTION.get(self.words_direction_dropdown.get())
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

        self.words_counter_text.update(f"{len(self.words_list)} Result{'s' if len(self.words_list) != 1 else ''}.")
        self.select_word_list.update(values=[f'{word[2]} ({word[3]})' for word in self.words_list])
        self.select_word()

    def select_word(self):
        select_word_list_indexes = self.select_word_list.get_indexes()
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

            self.word_appr_table.update(
                values=[(self.db.get_book_title(appr[0])[0], ) + appr for appr in appearances]
            )
        else:
            self.word_appr_table.update(values=[])

        if self.word_appr_table.TKTreeview.get_children():
            # Manually select the first appearance to be shown
            self.word_appr_table.TKTreeview.selection_set(1)  # This updates the GUI widget
            self.word_appr_table.SelectedRows = [0]  # This updates PySimpleGUI's rows logic
            self.select_word_appr()
        else:
            self.context_manager.hide_context()

    def select_word_appr(self):
        if self.word_appr_table.SelectedRows:
            selected_word_appr_row = self.word_appr_table.SelectedRows[0]
            if selected_word_appr_row < len(self.word_appr_table.Values):
                if self.word_appr_table.Values[selected_word_appr_row]:
                    (appr_book_name, appr_book_id, appr_line_offset, _appr_paragraph, appr_line) = \
                        self.word_appr_table.Values[selected_word_appr_row][0:5]

                    self.context_manager.set_context(appr_book_id, appr_line, appr_line_offset,
                                                     highlight_length=self.selected_word_length)

