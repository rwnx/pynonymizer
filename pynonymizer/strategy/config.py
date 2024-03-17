import os
from yaml import safe_load as load_yaml
from json import loads as load_json


class UnknownConfigTypeError(Exception):
    pass


def read_config(file_path):
    name, ext = os.path.splitext(os.path.basename(file_path))

    with open(file_path, "r") as config_data:
        if ext == ".yml" or ext == ".yaml":
            return load_yaml(config_data)
        elif ext == ".json":
            return load_json(config_data.read())
        else:
            raise UnknownConfigTypeError(f"Unknown config type {ext} from {file_path}")
