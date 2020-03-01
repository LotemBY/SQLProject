from enum import Enum, auto

import PySimpleGUI as sg

import gui.simple_gui_helper as sgh
from db.exceptions import NonUniqueError, CheckError
from gui.custom_tab import CustomTab

INVALID_GROUP_NAMES = ["none", "all"]


class InsertGroupTab(CustomTab):
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

        sg.SetOptions(font=(None, 20))
        self.groups_list = []
        self.selected_group_name = "Group"
        self.selected_group_id = None

        self.Layout([
            [self._create_group_column(), sg.VerticalSeparator(), self._create_word_column()]
        ])

    def _create_group_column(self):
        self.group_input = sg.InputText(
            size=(20, 1),
            font=sgh.INPUT_FONT,
            enable_events=True,
            text_color=sgh.INPUT_COLOR,
            key=InsertGroupTab.KEYS.GROUP_INPUT
        )
        insert_group_button = sg.Ok(
            button_text="Insert Group",
            key=InsertGroupTab.KEYS.INSERT_GROUP, size=(10, 1)
        )

        create_group_title = sg.Text(
            text="Create New Words Group",
            justification=sg.TEXT_LOCATION_CENTER,
            font=sgh.TITLE_FONT
        )
        self.group_error_text = sg.Text(
            text="",
            text_color=sgh.ERROR_TEXT_COLOR,
            auto_size_text=False
        )

        self.select_group_list = sg.Listbox(
            values=[""],
            auto_size_text=True,
            font=sgh.LIST_FONT,
            size=(30, 100),
            pad=(0, (0, 30)),
            select_mode=sg.SELECT_MODE_SINGLE,
            enable_events=True,
            key=InsertGroupTab.KEYS.GROUPS_LIST
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
            size=(20, 1),
            font=sgh.INPUT_FONT,
            enable_events=True,
            text_color=sgh.INPUT_COLOR,
            key=InsertGroupTab.KEYS.WORD_INPUT
        )

        insert_word_button = sg.Ok(
            button_text="Insert Word",
            key=InsertGroupTab.KEYS.INSERT_WORD,
            size=(10, 1)
        )

        self.add_words_title = sg.Text(
            text=f"Add Words to {self.selected_group_name}",
            auto_size_text=False,
            justification=sg.TEXT_LOCATION_CENTER,
            font=sgh.TITLE_FONT
        )

        self.words_error_text = sg.Text(
            text="",
            text_color=sgh.ERROR_TEXT_COLOR,
            auto_size_text=False
        )

        self.words_list = sg.Listbox(
            values=[""],
            auto_size_text=True,
            font=sgh.LIST_FONT,
            size=(30, 100),
            pad=(0, (0, 30)),
            select_mode=sg.SELECT_MODE_SINGLE,
            enable_events=True,
            key=InsertGroupTab.KEYS.WORDS_LIST
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

    @property
    def callbacks(self):
        return {
            InsertGroupTab.KEYS.GROUP_INPUT: self.clear_group_error,
            InsertGroupTab.KEYS.WORD_INPUT: self.clear_word_error,
            InsertGroupTab.KEYS.INSERT_GROUP: self.insert_group,
            InsertGroupTab.KEYS.GROUPS_LIST: self.select_group,
            InsertGroupTab.KEYS.INSERT_WORD: self.insert_word
        }

    def handle_enter(self, focused_element):
        if focused_element == self.group_input:
            self.insert_group()
        elif focused_element == self.word_input:
            self.insert_word()

    def clear_group_error(self):
        self.group_error_text.Update("")

    def insert_group(self):
        try:
            self.db.insert_words_group(self.group_input.get())
            self.group_input.Update("")

            # Select the newly added group
            self.select_group_list.Update(set_to_index=len(self.groups_list) - 1)
            self.select_group()
        except NonUniqueError:
            self.group_error_text.Update("Group already exists.")
        except CheckError:
            self.group_error_text.Update("Invalid group name.")

    def update_groups_list(self):
        self.groups_list = self.db.all_groups()
        self.select_group_list.Update(values=[group[1] for group in self.groups_list])

        # If we only have 1 item in the list, we should select it manually
        if len(self.groups_list) == 1:
            self.select_group_list.Update(set_to_index=0)
            self.select_group()

    def select_group(self):
        select_group_list_indexes = self.select_group_list.GetIndexes()
        if select_group_list_indexes:
            selected_group_row = select_group_list_indexes[0]
            if selected_group_row < len(self.groups_list):
                self.selected_group_id, self.selected_group_name = self.groups_list[selected_group_row]
                self.add_words_title.Update(value=f"Add Words to {self.selected_group_name}")
                self.update_words_list()

    def clear_word_error(self):
        self.words_error_text.Update("")

    def insert_word(self):
        if self.selected_group_id is not None:
            try:
                self.db.insert_word_to_group(self.selected_group_id, self.word_input.get())
                self.word_input.Update("")
            except NonUniqueError:
                self.words_error_text.Update("Word already exists.")
            except CheckError:
                self.words_error_text.Update("Invalid word.")
        else:
            self.words_error_text.Update("No group was selected.")

    def group_word_insertion_callback(self, group_id):
        if self.selected_group_id == group_id:
            self.update_words_list()

    def update_words_list(self):
        self.words_list.Update(values=self.db.words_in_group(self.selected_group_id))
