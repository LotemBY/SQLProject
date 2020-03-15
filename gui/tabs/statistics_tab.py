from enum import Enum, auto

import PySimpleGUI as sg

import db.sql_queries as queries
import gui.simple_gui_helper as sgh
from gui.tabs.custom_tab import CustomTab

ALL_BOOKS_FILTER = "> 0"


class StatisticsTab(CustomTab):
    class KEYS(Enum):
        SELECT_BOOK = auto()

    GENERAL_STATISTICS = (
        ("Total Books", queries.BOOKS_COUNT),
        ("Total Groups", queries.GROUPS_COUNT),
        ("Average Words in Group", queries.AVG_WORDS_PER_GROUP),
        ("Total Phrases", queries.PHRASES_COUNT),
        ("Average Words in Phrase", queries.AVG_WORDS_PER_PHRASE)
    )

    SPECIFIC_STATISTICS = (
        ("Total Words", queries.TOTAL_WORDS),
        ("Total Unique Words", queries.TOTAL_UNIQUE_WORDS),
        ("Total Letters", queries.TOTAL_LETTERS),
        ("Average Letters in Word", queries.AVG_LETTERS_PER_WORD)
    )

    SPECIFIC_STATISTICS_TEMPLATE = (
        ("Total {count_column}s", queries.TOTAL_COLUMN_COUNT),
        ("Average Words in {count_column}", queries.WORDS_COUNT),
        ("Average Letters in {count_column}", queries.LETTERS_COUNT)
    )

    def __init__(self, db):
        super().__init__(db, "Statistics", [[]])
        self.db.add_book_insert_callback(self.update_book_dropdown)
        self.db.add_group_insert_callback(self.refresh_general_statistics)
        self.db.add_group_word_insert_callback(self.refresh_general_statistics)
        self.db.add_phrase_insert_callback(self.refresh_general_statistics)

        self.book_id_filter = ALL_BOOKS_FILTER
        self.book_names_to_id = {}
        self.layout(
            [
                [sg.Sizer(v_pixels=20)],
                [self._create_general_statistics_frame()],
                [sg.Sizer(v_pixels=20)],
                [self._create_book_specific_statistics_frame()]
            ]
        )

    @staticmethod
    def create_elements(elements_list, title, query, font=sgh.MEDIUM_FONT_SIZE):
        result_text = sg.Text(text="0", size=(7, 1), pad=(0, 5), font=font, text_color=sgh.INPUT_COLOR)
        title_text = sg.Text(text=title + ": ", size=(25, 1), font=font)
        elements_list.append((title, result_text, query))
        return title_text, result_text

    def _create_general_statistics_frame(self):
        self.general_statistics = []

        statistic_lines = []
        for title, query in StatisticsTab.GENERAL_STATISTICS:
            title, result_text = self.create_elements(self.general_statistics, title, query, sgh.BIG_FONT_SIZE)
            statistic_lines.append([title, result_text])

        frame = sg.Frame(
            title="General Statistics",
            layout=statistic_lines
        )

        return frame

    def _create_book_specific_statistics_frame(self):
        search_book_txt = sg.Text(
            text="Select Book:",
            font=sgh.BIG_FONT_SIZE
        )

        self.books_dropdown = sg.Combo(
            values=["All"],
            default_value="All",
            readonly=True,
            size=(40, 1),
            font=sgh.BIG_FONT_SIZE,
            text_color=sgh.DROP_DOWN_TEXT_COLOR,
            background_color=sgh.NO_BG,
            enable_events=True,
            key=StatisticsTab.KEYS.SELECT_BOOK
        )

        self.specific_statistics = []
        first_rows = []
        for rows_counter, (title, query) in enumerate(StatisticsTab.SPECIFIC_STATISTICS):
            title_text, result_text = self.create_elements(self.specific_statistics, title, query, sgh.BIG_FONT_SIZE)

            first_rows.append([title_text, result_text])
            if rows_counter % 2 == 1:
                first_rows.append([sg.Sizer(v_pixels=20)])

        second_cols = []
        for column in "paragraph", "line", "sentence":
            col_rows = []
            for title, query in StatisticsTab.SPECIFIC_STATISTICS_TEMPLATE:
                title_text, result_text = self.create_elements(self.specific_statistics,
                                                               title.format(count_column=column.title()),
                                                               query.format(count_column=column))

                col_rows.append([title_text, result_text])
            second_cols.append(sg.Column(layout=col_rows))

        frame = sg.Frame(
            title="Book Statistics",
            layout=
            [
                [search_book_txt, self.books_dropdown],
                [sg.Sizer(v_pixels=30)]
            ] +
            first_rows +
            [
                [sg.Sizer(v_pixels=30)],
                sum([[col, sg.VerticalSeparator()] for col in second_cols], [])[:-1],
            ],
            element_justification=sgh.CENTER
        )

        return frame

    def reload_from_db(self):
        self.book_id_filter = ALL_BOOKS_FILTER
        self.update_book_dropdown()
        self.books_dropdown.update(value="All")

    @property
    def callbacks(self):
        return {
            StatisticsTab.KEYS.SELECT_BOOK: self.select_book,
        }

    def update_book_dropdown(self):
        books = self.db.all_books()
        self.book_names_to_id = {f'{title} by {author}': book_id for book_id, title, author, _path, _date in books}

        book_options = ["All"] + list(self.book_names_to_id.keys())
        self.books_dropdown.update(values=book_options, value=self.books_dropdown.get())

        self.refresh_general_statistics()

        # Update the specific statistics if "All" are selected
        if self.book_id_filter == ALL_BOOKS_FILTER:
            self.refresh_specific_statistics()

    def select_book(self):
        selected_book_id = self.book_names_to_id.get(self.books_dropdown.get())
        self.book_id_filter = ALL_BOOKS_FILTER if selected_book_id is None else f"== {selected_book_id}"
        self.refresh_specific_statistics()

    @staticmethod
    def get_result_str(cursor):
        # Fetch one result from the cursor and select the first column
        result = cursor.fetchone()[0]

        # If result is None, make it a zero
        if result is None:
            result = 0
        elif isinstance(result, float):
            # If result is float, round it to 3 digits
            result = round(result, 3)

            # If the result is a float which is a whole number, convert it to int
            if int(result) == result:
                result = int(result)

        return str(result)

    def refresh_general_statistics(self, _updated_group=None):
        for _text, result, query in self.general_statistics:
            result.update(value=self.get_result_str(self.db.execute(query)))

    def refresh_specific_statistics(self):
        for _text, result, query in self.specific_statistics:
            result.update(value=self.get_result_str(self.db.execute(query.format(book_id_filter=self.book_id_filter))))

    def refresh_statistics(self):
        self.refresh_general_statistics()
        self.refresh_specific_statistics()
