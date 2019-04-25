import database.mysql
from database.exceptions import UnknownDatabaseTypeError

def get_provider(type, *args, **kwargs):
    if type == "mysql":
        return database.mysql.MySqlProvider(*args)
    else:
        raise UnknownDatabaseTypeError(type)