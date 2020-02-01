INSERT INTO book(name, author, file_path, creation_date)
values (?, ?, ?, datetime(?, 'unixepoch'));