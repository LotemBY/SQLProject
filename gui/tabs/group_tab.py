from enum import Enum, auto

import PySimpleGUI as sg

import gui.simple_gui_helper as sgh
from db.exceptions import NonUniqueError, CheckError
from gui.tabs.custom_tab import CustomTab

INVALID_GROUP_NAMES = ["none", "all"]


class GroupTab(CustomTab):
    class KEYS(Enum):
        GROUP_INPUT = auto()
        WORD_INPUT = auto()
        INSERT_GROUP = auto()
        INSERT_WORD = auto()
        GROUPS_LIST = auto()
        WORDS_LIST = auto()

    def __init__(self, db):
        super().__init__(db, "Word Groups", [[]])
        self.db.add_group_insert_callback(self.update_groups_list)
        self.db.add_group_word_insert_callback(self.group_word_insertion_callback)

        self.groups_list = []
        self.selected_group_id = None

        self.layout([
            [sg.Sizer(h_pixels=5), self._create_group_column(), sg.VerticalSeparator(), self._create_word_column()]
        ])

    def _create_group_column(self):
        self.group_input = sg.InputText(
            size=(30, 1),
            font=sgh.MEDIUM_FONT_SIZE,
            enable_events=True,
            text_color=sgh.INPUT_COLOR,
            key=GroupTab.KEYS.GROUP_INPUT
        )
        insert_group_button = sg.Ok(
            button_text="Insert Group",
            key=GroupTab.KEYS.INSERT_GROUP, size=(10, 1)
        )

        create_group_title = sg.Text(
            text="Create New Words Group",
            justification=sg.TEXT_LOCATION_CENTER,
            font=sgh.TITLE_FONT_SIZE
        )
        self.group_error_text = sg.Text(
            text="",
            text_color=sgh.ERROR_TEXT_COLOR,
            auto_size_text=False
        )

        self.select_group_list = sg.Listbox(
            values=[""],
            auto_size_text=True,
            font=sgh.BIG_FONT_SIZE,
            size=(45, 100),
            pad=(0, (0, 30)),
            select_mode=sg.SELECT_MODE_SINGLE,
            enable_events=True,
            key=GroupTab.KEYS.GROUPS_LIST
        )

        col = sg.Column(
            layout=[
                [create_group_title],
                [self.group_input, insert_group_button],
                [self.group_error_text],
                [self.select_group_list]
            ],
            element_justification=sgh.CENTER
        )

        return col

    def _create_word_column(self):
        self.word_input = sg.InputText(
            size=(30, 1),
            font=sgh.MEDIUM_FONT_SIZE,
            enable_events=True,
            text_color=sgh.INPUT_COLOR,
            key=GroupTab.KEYS.WORD_INPUT
        )

        insert_word_button = sg.Ok(
            button_text="Insert Word",
            key=GroupTab.KEYS.INSERT_WORD,
            size=(10, 1)
        )

        self.add_words_title = sg.Text(
            text=f"Add Words to Group",
            auto_size_text=False,
            justification=sg.TEXT_LOCATION_CENTER,
            font=sgh.TITLE_FONT_SIZE
        )

        self.words_error_text = sg.Text(
            text="",
            text_color=sgh.ERROR_TEXT_COLOR,
            auto_size_text=False
        )

        self.words_list = sg.Listbox(
            values=[""],
            auto_size_text=True,
            font=sgh.BIG_FONT_SIZE,
            size=(45, 100),
            pad=(0, (0, 30)),
            select_mode=sg.SELECT_MODE_SINGLE,
            enable_events=True,
            key=GroupTab.KEYS.WORDS_LIST
        )

        col = sg.Column(
            layout=[
                [self.add_words_title],
                [self.word_input, insert_word_button],
                [self.words_error_text],
                [self.words_list]
            ],
            element_justification=sgh.CENTER
        )

        return col

    def reload_from_db(self):
        self.update_groups_list()
        self.add_words_title.update(value=f"Add Words to Group")
        self.update_words_list()

    @property
    def callbacks(self):
        return {
            GroupTab.KEYS.GROUP_INPUT: self.clear_group_error,
            GroupTab.KEYS.WORD_INPUT: self.clear_word_error,
            GroupTab.KEYS.INSERT_GROUP: self.insert_group,
            GroupTab.KEYS.GROUPS_LIST: self.select_group,
            GroupTab.KEYS.INSERT_WORD: self.insert_word
        }

    def handle_enter(self, focused_element):
        if focused_element == self.group_input:
            self.insert_group()
        elif focused_element == self.word_input:
            self.insert_word()

    def clear_group_error(self):
        self.group_error_text.update("")

    def insert_group(self):
        try:
            self.db.insert_words_group(self.group_input.get())
            self.group_input.update("")
            # Select the newly added group
            self.select_group_list.update(set_to_index=len(self.groups_list) - 1)
            self.select_group()
        except NonUniqueError:
            self.group_error_text.update("Group already exists.")
        except CheckError:
            self.group_error_text.update("Invalid group name.")

    def update_groups_list(self):
        self.groups_list = self.db.all_groups()
        self.select_group_list.update(values=[group[1] for group in self.groups_list])

        # If we only have 1 item in the list, we should select it manually
        if len(self.groups_list) == 1:
            self.select_group_list.update(set_to_index=0)
            self.select_group()

    def select_group(self):
        select_group_list_indexes = self.select_group_list.get_indexes()
        if select_group_list_indexes:
            selected_group_row = select_group_list_indexes[0]
            if selected_group_row < len(self.groups_list):
                self.selected_group_id, selected_group_name = self.groups_list[selected_group_row]
                self.add_words_title.update(value=f"Add Words to {selected_group_name}")
                self.update_words_list()

    def clear_word_error(self):
        self.words_error_text.update("")

    def insert_word(self):
        if self.selected_group_id is not None:
            try:
                self.db.insert_word_to_group(self.selected_group_id, self.word_input.get())
                self.word_input.update("")
            except NonUniqueError:
                self.words_error_text.update("Word already exists.")
            except CheckError:
                self.words_error_text.update("Invalid word.")
        else:
            self.words_error_text.update("No group was selected.")

    def group_word_insertion_callback(self, group_id):
        if self.selected_group_id == group_id:
            self.update_words_list()

    def update_words_list(self):
        self.words_list.update(values=[name for word_id, name in self.db.words_in_group(self.selected_group_id)])
