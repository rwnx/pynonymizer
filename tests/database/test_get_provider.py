import pytest
from unittest.mock import patch
from pynonymizer.database.exceptions import UnknownDatabaseTypeError
from pynonymizer.database import get_provider

@patch("pynonymizer.database.MySqlProvider")
def test_get_mysql_provider(mysql_provider):
    """
    given "mysql" type, get_provider should get a MySqlProvider
    """
    provider = get_provider("mysql", "db_host", "db_user", "db_password", "db_name")

    assert provider == mysql_provider.return_value


def test_get_unknown_provider():
    """
    get_provider should raise UnknownDatabaseTypeError if given unknown type
    """
    with pytest.raises(UnknownDatabaseTypeError) as e_info:
        provider = get_provider("UNKNOWN TYPE", "db_host", "db_user", "db_password", "db_name")