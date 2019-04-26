import os

class RawInput:
    def __init__(self, filename):
        self.filename = filename

    def get_size(self):
        return os.path.getsize(self.filename)

    def open(self):
        return open(self.filename)
