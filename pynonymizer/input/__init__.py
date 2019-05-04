from pynonymizer.input.gzip import GzipInput
from pynonymizer.input.raw import RawInput
import os


class UnknownInputTypeError(Exception):
    def __init__(self, filename):
        super().__init__("Unable to detect input type for file: {}".format(filename))


def from_location(filename):
    name, ext = os.path.splitext(filename)

    if ext == ".sql":
        return RawInput(filename)
    elif ext == ".gz":
        return GzipInput(filename)
    else:
        raise UnknownInputTypeError(filename)