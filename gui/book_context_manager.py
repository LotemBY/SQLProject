from tkinter.scrolledtext import ScrolledText

from gui import simple_gui_helper as sgh
from utils.utils import cached_read


class BookContextManager:
    def __init__(self, db, multiline_element, title_element):
        self.db = db
        self.multiline = multiline_element
        self.title = title_element
        self.curr_book_id = None

    def initialize(self):
        text_widget = self.multiline.TKText  # type: ScrolledText
        text_widget.tag_configure("highlight",
                                  foreground=sgh.WORD_HIGHLIGHT_TEXT_COLOR,
                                  background=sgh.WORD_HIGHLIGHT_BG_COLOR)
        text_widget.mark_set("highlightStart", "0.0")
        text_widget.mark_set("highlightEnd", "0.0")

    def hide_context(self):
        self.title.update(value="")
        self.multiline.update(value="")
        self.curr_book_id = None

    def _preview_book(self, book_id):
        if self.curr_book_id != book_id:
            self.title.update(value=self.db.get_book_full_name(book_id)[0])
            path = self.db.get_book_path(book_id)

            if not path:
                raise FileNotFoundError

            book_data = cached_read(path[0])
            self.multiline.update(value=book_data)
            self.curr_book_id = book_id

    def _set_multiline_highlight(self, start_line, start_line_offset, end_line, end_line_offset):
        text_widget = self.multiline.TKText  # type: ScrolledText
        start = "%d.%d" % (start_line, start_line_offset)
        end = "%d.%d" % (end_line, end_line_offset)
        text_widget.tag_remove("highlight", "highlightStart", "highlightEnd")
        text_widget.mark_set("highlightStart", start)
        text_widget.mark_set("highlightEnd", end)
        text_widget.tag_add("highlight", "highlightStart", "highlightEnd")
        text_widget.see("highlightStart")

    def set_context(self, book_id, start_line, start_line_offset, end_line=None, end_line_offset=None,
                    highlight_length=None):
        if highlight_length is not None and end_line is None and end_line_offset is None:
            end_line = start_line
            end_line_offset = start_line_offset + highlight_length

        try:
            self._preview_book(book_id)
        except FileExistsError:
            self.hide_context()
            return

        self._set_multiline_highlight(start_line, start_line_offset, end_line, end_line_offset)