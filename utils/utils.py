import codecs
import functools

ENCODINGS = "utf-8", None


def read_encoded_file(filename):
    for encoding in ENCODINGS:
        try:
            with codecs.open(filename, "r", encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            # Continue to next encoding
            pass

    return None


@functools.lru_cache()
def cached_read(filename):
    return read_encoded_file(filename)
