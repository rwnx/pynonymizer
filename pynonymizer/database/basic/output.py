import gzip
import os


class UnknownOutputTypeError(Exception):
    def __init__(self, filename):
        super().__init__("Unable to detect output type for file: {}".format(filename))


class GzipOutput:
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        return gzip.open(self.filename, "wb")


class RawOutput:
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        return open(self.filename, "wb")


def resolve_output(filename):
    name, ext = os.path.splitext(filename)

    if ext == ".sql":
        return RawOutput(filename)
    elif ext == ".gz":
        return GzipOutput(filename)
    else:
        raise UnknownOutputTypeError(filename)