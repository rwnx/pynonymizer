import os
import uuid
from pynonymizer.database.mysql import MySqlProvider
from pynonymizer.database.mssql import MsSqlProvider
from pynonymizer.database.postgres import PostgreSqlProvider
from pynonymizer.database.exceptions import UnknownDatabaseTypeError

def get_temp_db_name(filename=None):
    name, _ = os.path.splitext(os.path.basename(filename))
    return f"{name}_{uuid.uuid4().hex}"


def get_provider(type, *args, **kwargs):
    provider = None

    if type == "mysql":
        provider = MySqlProvider
    if type == "mssql":
        provider = MsSqlProvider
    elif type == "postgres":
        provider = PostgreSqlProvider

    if provider:
        return provider(*args, **kwargs)
    else:
        raise UnknownDatabaseTypeError(type)
