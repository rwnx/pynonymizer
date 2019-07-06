from abc import ABC, abstractmethod

class InputSource(ABC):
    @property
    @abstractmethod
    def size(self):
        """
        Get the raw size for progress when streaming
        """
        pass

    @property
    @abstractmethod
    def filepath(self):
        """
        Unpack/process/download and present a tempfile for non-streamable restores
        """
        pass

    @property
    def streamable(self):
        """
        determine if a source supports streaming
        """
        return False

    @abstractmethod
    def open(self):
        """
        open a file-like object that gives the resource to stream.
        :return:
        """
        pass