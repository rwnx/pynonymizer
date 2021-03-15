import gzip
import lzma
import os
import sys
"""
Streaming output files for streamable providers
"""


class UnknownOutputTypeError(Exception):
    def __init__(self, filename):
        super().__init__("Unable to detect output type for file: {}".format(filename))


class GzipOutput:
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        return gzip.open(self.filename, "wb")

class XzOutput:
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        return lzma.open(self.filename, "wb")

class RawOutput:
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        return open(self.filename, "wb")

class StdOutOutput:
    def open(self):
        return sys.stdout.buffer

def resolve_output(filename):
    if filename == "-":
        return StdOutOutput()

    name, ext = os.path.splitext(filename)

    if ext == ".sql":
        return RawOutput(filename)
    elif ext == ".gz":
        return GzipOutput(filename)
    elif ext == ".xz":
        return XzOutput(filename)
    else:
        raise UnknownOutputTypeError(filename)