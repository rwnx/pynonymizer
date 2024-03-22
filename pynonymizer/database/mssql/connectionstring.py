# coding: utf-8

# url='https://github.com/bgusach/pyconstring',

# The MIT License (MIT)

# Copyright (c) 2014 ikaros45

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import unicode_literals

import sys

from collections import OrderedDict
from operator import methodcaller


__all__ = ["ConnectionString"]
__version__ = "0.5.0"


class ConnectionString(OrderedDict):
    def __init__(self, *args, **kwargs):
        self._formatted_prio_keys = {
            self._format_key(k) for k in self._non_overridable_keys
        }
        super(ConnectionString, self).__init__(*args, **kwargs)

    # Keys that won't be overridden if they appear more than once in the connection string to be loaded
    _non_overridable_keys = ["Provider"]
    _format_key = staticmethod(methodcaller("title"))

    @classmethod
    def from_string(cls, string):
        """
        Creates a new instance and loads the passed string

        :param unicode string: connection string to be parsed
        :rtype: ConnectionString

        """
        self = cls()
        self._store_items(
            self._parse_string(string.lstrip()), allow_prio_overriding=False
        )

        return self

    def _store_items(self, items, allow_prio_overriding=True):
        """
        Stores key-val items

        :param bool allow_prio_overriding: flag to allow overriding of priority keys

        """
        pred = (lambda k: True) if allow_prio_overriding else self._no_prio_conflict

        self.update((k, v) for k, v in items if pred(k))

    def __setitem__(self, key, value, *args, **kwargs):
        super(ConnectionString, self).__setitem__(
            self._format_key(key), value, *args, **kwargs
        )

    def _no_prio_conflict(self, key):
        """
        Returns whether the key can be set or not taking into account that priority keys cannot be overridden

        :rtype: bool

        """
        return key not in self._formatted_prio_keys or key not in self

    @classmethod
    def _parse_string(cls, string):
        """
        Parses the string and returns an iterable of tuples (key, value)

        :raises: ValueError

        """
        while string:
            key, string = cls._get_key_from_string(string)
            value, string = cls._get_value_from_string(string)
            yield key, value

    @classmethod
    def _get_key_from_string(cls, string):
        """
        Receives a leftstripped string, identifies the heading key, and returns a tuple (key, rest of the string)

        :param unicode string: substring of connection string
        :returns: rest of string left stripped and without any leading '='
        :rtype: unicode

        """
        start = 0
        while True:
            pos = string.find("=", start)
            if pos == -1:
                raise ValueError('Token delimiter not found: "="')

            if string[pos + 1 : pos + 2] == "=":
                start = pos + 2
                continue

            key, rest = string[:pos], string[pos + 1 :]
            return cls._decode_key(key), rest.lstrip()

    _quotes = {'"', "'"}

    @classmethod
    def _get_value_from_string(cls, string):
        """
        Receives a left stripped string, identifies the heading value, decodes it,
        and returns a tuple (key, rest of the string)

        :param unicode string: substring of connection string
        :returns: rest of string left stripped and without any leading ';'
        :rtype: unicode
        :raises: ValueError

        """
        # Not starting with quotes
        first = string[0]
        if first not in cls._quotes:
            value, _, string = string.partition(";")
            return value.rstrip(), string

        start = 1
        while True:
            pos = string.find(first, start)
            if pos == -1:
                raise ValueError('Token delimiter not found: "%s"' % first)

            # If it is a double quote, skip and keep searching
            if string[pos] == string[pos + 1]:
                start = pos + 2
                continue

            value, rest = string[: pos + 1], string[pos + 1 :]
            return cls._decode_value(value.rstrip()), rest.lstrip(" ;")

    @staticmethod
    def _decode_key(key):
        if not key:
            raise ValueError("Key cannot be empty string")

        return key.strip().replace("==", "=")

    @staticmethod
    def _encode_key(key):
        if not key:
            raise ValueError("Key cannot be empty string")

        return key.strip().replace("=", "==")

    @classmethod
    def _decode_value(cls, val):
        val = val.strip()

        if not val:
            return val

        # If it does not start with quotes, no decoding needed
        start = val[0]
        if start not in cls._quotes:
            return val

        # Remove wrapping quotes, and reduce any double inner quote
        return val[1:-1].replace(start * 2, start)

    @classmethod
    def _encode_value(cls, val):
        if not val:
            return val

        # No special characters that would require quoting
        if not (
            val.startswith(" ")
            or val.endswith(" ")
            or ";" in val
            or val[0] in cls._quotes
        ):
            return val

        # Get what kind of quotes are present in value
        quotes_in_val = cls._quotes.intersection(val)

        if not quotes_in_val:
            return '"%s"' % val

        if len(quotes_in_val) == 1:
            return "{quote}{val}{quote}".format(
                val=val, quote=cls._quotes.difference(quotes_in_val).pop()
            )

        # If both types of quotes in string, escape the double quotes by doubling them
        return '"%s"' % val.replace('"', '""')

    def translate(self, trans, strict=True):
        """
        Translates the keys of the store.

        :param dict trans: translation mapping {pre name: post name}
        :param bool strict: When strict, the existing keys in self that
                            are not in `trans` will be removed. If not strict,
                            they will still exist.

        """
        trans = {self._format_key(key): value for key, value in trans.items()}
        pred = trans.__contains__ if strict else lambda x: True

        translated_items = [
            (trans.get(key, key), value) for key, value in self.items() if pred(key)
        ]

        self.clear()
        self._store_items(translated_items)

    def get_string(self):
        """
        :returns: the composed connection string
        :rtype: unicode

        """
        if not self:
            return ""

        return (
            ";".join(
                "%s=%s" % (self._encode_key(k), self._encode_value(v))
                for k, v in self.items()
            )
            + ";"
        )

    def __unicode__(self):
        return self.get_string()

    def __str__(self):
        return (
            self.get_string()
            if sys.version_info > (3, 0)
            else self.get_string().encode("utf-8")
        )

    def __repr__(self):
        return "<ConnectionString '%s'>" % self.get_string()

    __getitem__ = lambda self, key: super(ConnectionString, self).__getitem__(
        self._format_key(key)
    )
    __delitem__ = lambda self, key: super(ConnectionString, self).__delitem__(
        self._format_key(key)
    )
    __contains__ = lambda self, key: super(ConnectionString, self).__contains__(
        self._format_key(key)
    )
