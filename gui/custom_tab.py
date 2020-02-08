import PySimpleGUI as sg


class CustomTab(sg.Tab):
    @property
    def callbacks(self):
        return {}

    def handle_event(self, event):
        self.callbacks.get(event, lambda _: None)()
