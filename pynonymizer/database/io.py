from io import TextIOWrapper
import os
import struct
import gzip
import sys
import lzma


class UnknownInputTypeError(Exception):
    def __init__(self, filename):
        super().__init__("Unable to detect input type for file: {}".format(filename))


class UnknownOutputTypeError(Exception):
    def __init__(self, filename):
        super().__init__("Unable to detect output type for file: {}".format(filename))


def read_until_empty_byte(data, chunk_size):
    reader = lambda: data.read(chunk_size)

    return iter(reader, b"")


def dump(progress, write_path, source, size, chunk_size=8192):
    close_writer = True
    if write_path == "-":
        output_obj = sys.stdout.buffer
        close_writer = False
    else:
        name, ext = os.path.splitext(write_path)

        if ext == ".sql":
            output_obj = open(write_path, "wb")
        elif ext == ".gz":
            output_obj = gzip.open(write_path, "wb")
        elif ext == ".xz":
            output_obj = lzma.open(write_path, "wb")
        else:
            raise UnknownOutputTypeError(write_path)

    # TODO: replace with context manager?
    try:
        with progress(
            desc="Dumping",
            total=size,
            unit="B",
            unit_scale=True,
            unit_divisor=1000,
        ) as bar:
            for chunk in read_until_empty_byte(source, chunk_size):
                output_obj.write(chunk)
                bar.update(len(chunk))
    finally:
        if close_writer:
            output_obj.close()


def restore(progress, read_path, target, chunk_size=8192):
    if read_path == "-":
        input_obj = sys.stdin.buffer
        dumpsize = 0

    else:
        name, ext = os.path.splitext(read_path)

        if ext == ".sql":
            input_obj = open(read_path, "rb")
            dumpsize = os.path.getsize(read_path)
        elif ext == ".gz":
            input_obj = gzip.open(read_path, "rb")
            """
            Get the uncompressed filesize of a gzip
            The last 4 bytes of a gzip contain the uncompressed filesize in little endian format (broken on >4GB zips)
            :param filename: gzip filename to read from
            :returns uncompressed gzip filesize.
            """
            with open(read_path, "rb") as file:
                file.seek(-4, 2)
                rawsize = file.read()
                dumpsize = struct.unpack("<I", rawsize)[0]
        else:
            raise UnknownInputTypeError(read_path)

    with progress(
        desc="Restoring",
        total=dumpsize,
        unit="B",
        unit_scale=True,
        unit_divisor=1000,
    ) as bar:
        for chunk in read_until_empty_byte(input_obj, chunk_size):
            target.write(chunk)
            target.flush()
            bar.update(len(chunk))
