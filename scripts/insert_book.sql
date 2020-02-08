INSERT INTO book(title, author, file_path, creation_date)
values (?, ?, ?, datetime(?, 'unixepoch'));