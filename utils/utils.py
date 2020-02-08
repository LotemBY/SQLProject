import functools


@functools.lru_cache()
def cached_read(filename):
    with open(filename, "r") as file:
        return file.read()
