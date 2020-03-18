from datetime import datetime
from itertools import count
from xml.etree.ElementTree import ElementTree, Element

from lxml import etree

from db.books_db import BookDatabase
from utils.constants import XML_DATE_FORMAT

SCHEMA_FILENAME = r"db\xml\schema.xsd"

# Parser singleton
g_parser = None


def parse_xml(xml_path):  # type: (str) -> ElementTree
    global g_parser

    if g_parser is None:
        schema = etree.XMLSchema(etree.parse(SCHEMA_FILENAME))
        g_parser = etree.XMLParser(schema=schema)

    return etree.ElementTree(file=xml_path, parser=g_parser)


def init_words(db, words_root):  # type: (BookDatabase, Element) -> None
    words = ((word.text, word.get("id")) for word in words_root)
    db.insert_many_words_with_id(words)


def init_books(db, books_root):  # type: (BookDatabase, Element) -> None
    for book in books_root:
        title = book.find("title").text
        author = book.find("author").text
        path = book.find("path").text
        size = int(book.find("size").text)
        date = datetime.strptime(book.find("date").text, XML_DATE_FORMAT)
        book_id = db.insert_book(title, author, path, size, date)

        appearances = []
        word_index_counter = count(1)
        sentence_counter = count(1)
        line_index_counter = count(1)
        curr_line = None
        for paragraph, paragraph_element in enumerate(book.find("body"), start=1):
            for sentence_element in paragraph_element:
                sentence = next(sentence_counter)

                for sentence_index, wordref in enumerate(sentence_element, start=1):
                    word_id = int(wordref.get("refid"))
                    line, line_offset = (int(n) for n in wordref.text.split(":"))

                    if curr_line != line:
                        line_index_counter = count(1)
                    curr_line = line

                    appearances.append((book_id,
                                        word_id,
                                        next(word_index_counter),
                                        paragraph,
                                        line,
                                        next(line_index_counter),
                                        line_offset,
                                        sentence,
                                        sentence_index))

        db.insert_many_word_id_appearances(appearances)


def init_groups(db, groups_root):  # type: (BookDatabase, Element) -> None
    for group in groups_root:
        group_id = db.insert_words_group(group.find("name").text)
        db.insert_many_word_ids_to_group(group_id, (int(wordref.text) for wordref in group.iter("wordref")))


def init_phrases(db, phrases_root):  # type: (BookDatabase, Element) -> None
    for phrase in phrases_root:
        phrase_id = db.insert_phrase(phrase.find("text").text, len(phrase))
        db.insert_many_word_ids_to_phrase(phrase_id, (int(wordref.text) for wordref in phrase.iter("wordref")))


def import_db(db, xml_path):  # type: (BookDatabase, str) -> None
    try:
        tree = parse_xml(xml_path)
    except etree.XMLSyntaxError as e:
        raise ValueError(e.msg)

    db.new_connection()
    root = tree.getroot()
    init_words(db, root.find("words"))
    init_books(db, root.find("books"))
    init_groups(db, root.find("groups"))
    init_phrases(db, root.find("phrases"))
