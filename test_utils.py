from Stater.utils import get_server_params
import pytest


def test_get_server_params():
    get_server_params(
        components={"hello": {"code": 0}, "test": {"status": 2}})


def test_get_server_params_2():
    with pytest.raises(ValueError):
        get_server_params(repo_url="hello")


def test_get_server_params_3():
    get_server_params(repo_url="http://github.com/mithem/test")
