import re
import pytest
from contextlib import contextmanager


class AnyObject:
    def __eq__(self, actual):
        return True

    def __ne__(self, other):
        return False


class SuperdictOf:
    def __init__(self, required_dict):
        self.required_dict = required_dict

    def __eq__(self, actual):
        return self.required_dict.items() <= actual.items()

    def __ne__(self, actual):
        return not(self.required_dict.items() <= actual.items())



class ComparableRegex:
    """Assert that a given string meets some expectations."""

    def __init__(self, pattern, flags=0):
        self._regex = re.compile(pattern, flags)

    def __eq__(self, actual):
        return bool(self._regex.match(actual))

    def __repr__(self):
        return self._regex.pattern


@contextmanager
def not_raises(exception):
    try:
        yield
    except exception:
        raise pytest.fail("DID RAISE {0}".format(exception))


def list_rindex(alist, value):
  return len(alist) - alist[-1::-1].index(value) - 1