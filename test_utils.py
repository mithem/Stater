from Stater.utils import get_server_params


def test_get_server_params():
    get_server_params(
        components={"hello": {"code": 0}, "test": {"status": 2}})
