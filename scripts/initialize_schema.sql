create table if not exists book (
    book_id integer not null primary key,
    name text not null,
    author text,
    file_path text not null unique,
    creation_date date
);

create table if not exists word (
    word_id integer not null primary key,
    name text not null unique,
    length integer default 0
);

create trigger if not exists word_length_insertion
   after insert
   on word
   for each row
begin
   update word set length = length(name) where word_id = NEW.word_id;
end;

create table if not exists word_appearance (
    word_index integer not null,
    book_id integer not null,
    word_id integer not null,
    paragraph integer not null,
    line integer not null,
    line_index integer not null,
    sentence integer not null,
    sentence_index integer not null,
    offset integer not null,
    primary key(word_index, book_id, word_id),
    foreign key(book_id) references book,
    foreign key(word_id) references word
);

--INSERT OR IGNORE INTO word(word) values ("Hi"), ("Lotem"), ("Rotem");

-- INSERT INTO word_appearance(word_index, book_id, word_id, paragraph, line, line_index, sentence, sentence_index)
--VALUES (0, 0, (SELECT word_id FROM word WHERE word == ?), 0, 0, 0, 0, 0)

-- SELECT word_id FROM word WHERE word == "lotem"