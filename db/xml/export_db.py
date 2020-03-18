from xml.dom import minidom
from xml.etree.ElementTree import ElementTree, Element, Comment, SubElement, tostring

from db.books_db import BookDatabase
from utils.constants import XML_DATE_FORMAT
from utils.utils import timeit


def prettify(elem):
    rough_string = tostring(elem, 'utf-8')
    return minidom.parseString(rough_string).toprettyxml(indent="  ")


@timeit
def export_words(db):  # type: (BookDatabase) -> Element
    words = Element('words')
    for word_id, name in db.all_words():
        SubElement(words, "word", {"id": str(word_id)}).text = name

    return words


@timeit
def export_books(db):  # type: (BookDatabase) -> Element
    books = Element('books')
    for book_id, title, author, path, size, date in db.all_books(date_format=XML_DATE_FORMAT):
        book = SubElement(books, "book")
        SubElement(book, "title").text = title
        SubElement(book, "author").text = author
        SubElement(book, "path").text = path
        SubElement(book, "size").text = str(size)
        SubElement(book, "date").text = date
        body = SubElement(book, "body")

        curr_paragraph = None
        curr_paragraph_element = None
        curr_sentence = None
        curr_sentence_element = None
        for word_appr in db.all_book_words(book_id):
            word_id, paragraph, sentence, line, line_offset = word_appr

            if curr_paragraph is None or curr_paragraph < paragraph:
                curr_paragraph_element = SubElement(body, "paragraph")
            curr_paragraph = paragraph

            if curr_sentence is None or curr_sentence < sentence:
                curr_sentence_element = SubElement(curr_paragraph_element, "sentence")
            curr_sentence = sentence

            # appr = SubElement(curr_sentence_element, "appr", {"pos": f"{line}:{line_offset}"})
            SubElement(curr_sentence_element, "appr", {"refid": str(word_id)}).text = f"{line}:{line_offset}"

    return books


@timeit
def export_groups(db):  # type: (BookDatabase) -> Element
    groups = Element('groups')
    for group_id, name in db.all_groups():
        group = SubElement(groups, "group")
        SubElement(group, "name").text = name

        # group.text = ' '.join(str(word_id) for word_id, _name in db.words_in_group(group_id))
        for word_id, _name in db.words_in_group(group_id):
            SubElement(group, "wordref").text = str(word_id)

    return groups


@timeit
def export_phrases(db):  # type: (BookDatabase) -> Element
    phrases = Element('phrases')
    for phrase_text, phrase_id in db.all_phrases():
        phrase = SubElement(phrases, "phrase")
        SubElement(phrase, "text").text = phrase_text

        for word_id, in db.words_in_phrase(phrase_id):
            SubElement(phrase, "wordref").text = str(word_id)

    return phrases


@timeit
def build_xml(db):  # type: (BookDatabase) -> ElementTree
    root = Element('tables')

    comment = Comment('Books Database by Lotem Ben Yaakov')
    root.append(comment)

    root.append(export_words(db))
    root.append(export_books(db))
    root.append(export_groups(db))
    root.append(export_phrases(db))

    return ElementTree(root)


@timeit
def export_db(db, xml_path, prettify=False):
    tree = build_xml(db)

    with open(xml_path, "wb") as xml_output:
        if prettify:
            xml_output.write(bytes(minidom.parseString(tostring(tree.getroot())).toprettyxml(indent=" " * 4), 'utf-8'))
        else:
            tree.write(xml_output, encoding='utf-8', xml_declaration=True)
