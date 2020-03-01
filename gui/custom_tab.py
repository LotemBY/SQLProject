import PySimpleGUI as sg

import gui.simple_gui_helper as sgh
from db.books_db import BookDatabase


class CustomTab(sg.Tab):
    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ElementJustification = sgh.CENTER
        self.db = db  # type: BookDatabase

    def initialize(self):
        pass

    @property
    def callbacks(self):
        return {}

    def handle_enter(self, focused_element):
        pass

    def handle_event(self, event):
        self.callbacks.get(event, lambda: None)()
