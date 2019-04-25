import struct
import gzip

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
        return gzip.open(self.filename)
