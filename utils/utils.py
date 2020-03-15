import codecs
import functools
import time

ENCODINGS = "utf-8", None


def open_encoded_file(filename):
    for encoding in ENCODINGS:
        try:
            return codecs.open(filename, "r", encoding=encoding)
        except UnicodeDecodeError:
            # Continue to next encoding
            pass

    return None


@functools.lru_cache()
def cached_read(filename):
    with open_encoded_file(filename) as file:
        return file.read()


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result

    return timed
