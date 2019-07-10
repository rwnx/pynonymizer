import os
import uuid
from pynonymizer.database.mysql import MySqlProvider
from pynonymizer.database.mssql import MsSqlProvider
from pynonymizer.database.exceptions import UnknownDatabaseTypeError

def get_temp_db_name(filename=None):
    name, _ = os.path.splitext(os.path.basename(filename))
    return f"{name}_{uuid.uuid4().hex}"


def get_provider(type, *args, **kwargs):
    if type == "mysql":
        return MySqlProvider(*args, **kwargs)
    if type == "mssql":
        return MsSqlProvider(*args, **kwargs)
    else:
        raise UnknownDatabaseTypeError(type)
