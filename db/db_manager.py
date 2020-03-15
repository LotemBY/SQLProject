import os
import sqlite3

from db.exceptions import raise_specific_exception
from utils.utils import cached_read


def raise_specific_exception_wrapper(func):
    def _inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as error:
            raise_specific_exception(error)

    return _inner


class Database:
    SCRIPTS_DIR = r"scripts"

    def __init__(self, db_path=None, always_create=False):
        self._conn = None  # type: sqlite3.Connection
        self._cursor = None  # type: sqlite3.Cursor
        self.new_connection(always_create, db_path)

    def save_to_file(self, db_path, switch_to_new=False):
        disk_conn = sqlite3.connect(db_path)
        self.commit()
        self._conn.backup(disk_conn)

        if switch_to_new:
            self.close(commit=False)
            self._conn = disk_conn
            self._cursor = self._conn.cursor()

    def new_connection(self, always_create=True, db_path=None, commit=True):
        if self._conn:
            self.close(commit=commit)

        if db_path:
            already_exists = os.path.exists(db_path)
            if always_create and already_exists:
                os.remove(db_path)
        else:
            already_exists = False

        self._conn = sqlite3.connect(db_path if db_path else ':memory:')
        self._cursor = self._conn.cursor()

        # Return if a new db was created
        return already_exists and not always_create

    @raise_specific_exception_wrapper
    def execute(self, *args, **kwargs):
        return self._cursor.execute(*args, **kwargs)

    @raise_specific_exception_wrapper
    def executemany(self, *args, **kwargs):
        return self._cursor.executemany(*args, **kwargs)

    @raise_specific_exception_wrapper
    def executescript(self, *args, **kwargs):
        return self._cursor.executescript(*args, **kwargs)

    @staticmethod
    def read_script_file(file_name):
        path = os.path.join(Database.SCRIPTS_DIR, file_name + '.sql')
        return cached_read(path)

    def run_sql_file(self, file_name, args=(), multiple_statements=False):
        script_data = Database.read_script_file(file_name)

        try:
            if multiple_statements:
                return self.executescript(script_data)
            else:
                return self.execute(script_data, args)
        except sqlite3.Error as error:
            raise_specific_exception(error)

    def commit(self):
        return self._conn.commit()

    def close(self, commit=True):
        if commit:
            self.commit()

        if self._cursor:
            self._cursor.close()

        if self._conn:
            self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self.close()
