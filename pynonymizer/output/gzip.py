import gzip

class GzipOutput:
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        return gzip.open(self.filename, "wb")
