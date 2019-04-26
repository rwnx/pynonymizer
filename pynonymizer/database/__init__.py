from pynonymizer.database.mysql import MySqlProvider
from pynonymizer.database.exceptions import UnknownDatabaseTypeError

def get_provider(type, *args, **kwargs):
    if type == "mysql":
        return MySqlProvider(*args)
    else:
        raise UnknownDatabaseTypeError(type)