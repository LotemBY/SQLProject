create table if not exists book (
    book_id integer not null primary key,
    title text not null,
    author text not null,
    file_path text not null unique,
--    creation_date date,
    unique(title, author),
    check(title <> ''),
    check(author <> ''),
    check(file_path <> '')
);

create table if not exists word (
    word_id integer not null primary key,
    name text not null unique,
    length integer default 0,
    check(name <> '')
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
    line_offset integer not null,
    sentence integer not null,
    sentence_index integer not null,
    primary key(word_index, book_id, word_id),
    foreign key(book_id) references book,
    foreign key(word_id) references word
);

create table if not exists words_group (
    group_id integer not null primary key,
    name text not null unique,
    check(name <> '')
);

create table if not exists word_in_group (
    group_id integer not null,
    word_id integer not null,
    primary key(group_id, word_id),
    foreign key(group_id) references words_group,
    foreign key(word_id) references word
);

create table if not exists phrase (
    phrase_id integer not null primary key,
    words_count integer not null CHECK(words_count > 1)
);

create table if not exists word_in_phrase (
    phrase_id integer not null,
    word_id integer not null,
    phrase_index integer not null,
    primary key(phrase_id, word_id, phrase_index),
    foreign key(phrase_id) references phrase,
    foreign key(word_id) references word
);