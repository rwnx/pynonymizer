from pynonymizer.output.gzip import GzipOutput
from pynonymizer.output.raw import RawOutput
import os


class UnknownOutputTypeError(Exception):
    def __init__(self, filename):
        super().__init__("Unable to detect output type for file: {}".format(filename))


def from_location(filename):
    name, ext = os.path.splitext(filename)

    if ext == ".sql":
        return RawOutput(filename)
    elif ext == ".gz":
        return GzipOutput(filename)
    else:
        raise UnknownOutputTypeError(filename)