import os
import struct
import gzip
import sys
"""
Streaming input files for streamable providers
"""


class UnknownInputTypeError(Exception):
    def __init__(self, filename):
        super().__init__("Unable to detect input type for file: {}".format(filename))


class GzipInput:
    def __init__(self, filename):
        self.filename = filename

    def get_size(self):
        """
        Get the uncompressed filesize of a gzip
        The last 4 bytes of a gzip contain the uncompressed filesize in little endian format (broken on >4GB zips)
        :param filename: gzip filename to read from
        :returns uncompressed gzip filesize.
        """
        with open(self.filename, 'rb') as file:
            file.seek(-4, 2)
            size = file.read()
            return struct.unpack('<I', size)[0]

    def open(self):
        return gzip.open(self.filename, "rb")


class RawInput:
    def __init__(self, filename):
        self.filename = filename

    def get_size(self):
        return os.path.getsize(self.filename)

    def open(self):
        return open(self.filename, "rb")

class StdInInput:
    def get_size(self):
        return None

    def open(self):
        return sys.stdin.buffer


def resolve_input(filename):
    if filename == "-":
        return StdInInput()

    name, ext = os.path.splitext(filename)

    if ext == ".sql":
        return RawInput(filename)
    elif ext == ".gz":
        return GzipInput(filename)
    else:
        raise UnknownInputTypeError(filename)