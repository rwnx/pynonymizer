class RawOutput:
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        return open(self.filename, "wb")
