from output.gzip import GzipOutput
from output.raw import RawOutput
import os


class UnknownOutputTypeError(Exception):
    def __init__(self, filename):
        super().__init__("Unable to detect output type for file: {}".format(filename))


def get_output(filename):
    name, ext = os.path.splitext(filename)

    if ext == ".sql":
        return RawOutput(filename)
    elif ext == ".gz":
        return GzipOutput(filename)
    else:
        raise UnknownOutputTypeError(filename)