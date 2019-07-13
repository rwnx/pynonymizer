import pytest
from unittest.mock import Mock, patch, mock_open
from pynonymizer.strategy.config import read_config, UnknownConfigTypeError

test_path_examples = [
    "",
    "complex/multi/part/path/test/",
    "complex\\multi\\part\\path\\test\\",
    "/absolute/path/test/",
    "C:\\absolute\\path\\test\\"
]


@pytest.mark.parametrize("path_example", test_path_examples)
@patch("builtins.open")
@patch("pynonymizer.strategy.config.load_yaml")
@patch("pynonymizer.strategy.config.load_json")
def test_read_config_json(load_json, load_yaml, open, path_example):
    filepath = path_example + "test.json"
    config = read_config(filepath)
    load_json.assert_called_once_with( open().__enter__().read() )
    assert config == load_json()


@pytest.mark.parametrize("path_example", test_path_examples)
@patch("builtins.open")
@patch("pynonymizer.strategy.config.load_yaml")
@patch("pynonymizer.strategy.config.load_json")
def test_read_config_yml(load_json, load_yaml, open, path_example):
    filepath = path_example + "test.yml"
    config = read_config(filepath)
    load_yaml.assert_called_once_with(open().__enter__())
    assert config == load_yaml()


@pytest.mark.parametrize("path_example", test_path_examples)
@patch("builtins.open")
@patch("pynonymizer.strategy.config.load_yaml")
@patch("pynonymizer.strategy.config.load_json")
def test_read_config_yaml(load_json, load_yaml, open, path_example):
    filepath = path_example + "test.yaml"
    config = read_config(filepath)
    load_yaml.assert_called_once_with(open().__enter__())
    assert config == load_yaml()


@pytest.mark.parametrize("path_example", test_path_examples)
@patch("builtins.open")
@patch("pynonymizer.strategy.config.load_yaml")
@patch("pynonymizer.strategy.config.load_json")
def test_read_config_unknown(load_json, load_yaml, open, path_example):
    with pytest.raises(UnknownConfigTypeError):
        filepath = path_example + "test.bbs"
        config = read_config(filepath)