import re
import json
from hashlib import sha256
import datetime
from fileloghelper import Logger

logger = Logger("utils.log", "utils", True, True)


def get_server_params(name: str = None, description: str = None, repo_url: str = None, main_status: int = None, components: dict = None, password: str = None):
    """check args for user errors and return components: str (in json format), encrypted_password: str, djoined: str"""
    if name == None:
        name = "validname"
    if description == None:
        description = ""
    if repo_url == None:
        repo_url = "https://valid.test"
    if main_status == None:
        main_status = 0
    if components == None:
        components = {}
    if password == None:
        password = "abcdefg12345678"

    if len(name) > 20:
        raise ValueError("name argument too long (max 20)")
    if len(name) < 4:
        raise ValueError("name too short")
    if not re.match("^[a-z_][a-z_.-]", name) or "#" in name:
        raise ValueError("Username invalid.")
    if len(description) > 1024:
        raise ValueError("description argument too long")
    if not re.match("^https?://(www\.)?[\w.]+\.\w{2,}[a-zA-Z/_.-]*$", repo_url):
        raise ValueError("repo_url argument invalid.")
    if type(main_status) != int:
        raise TypeError("'main_status' expected to be of type int.")
    if main_status < 0 or main_status > 3:
        raise ValueError("main_status argument not 0, 1, 2, or 3")
    if type(components) != dict:
        raise TypeError("components is not a dict.")
    elif type(components) == dict:
        for key, value in components.items():
            if type(value) != dict:
                raise TypeError(
                    "(One) component in components: dict is not of type dict")
            name = key
            get_server_params(name)
            description = value.get("description", "NOTADESCRIPTION")
            status = value.get("status", "NOTFOUND")
            if status == "NOTFOUND":
                status = value.get("code", -1)
                if status != -1:
                    del value["code"]
                    value["status"] = status
            if name == "NOTANAME":
                raise ValueError(
                    "name attribute of one component not specified.")
            if type(name) != str:
                raise TypeError(
                    "name attribute of one component not of type str")
            if type(status) != int:
                raise TypeError(
                    "status attribute of one component invalid (excepted int between 0 and 3 (both included, see docs))")
            if status == -1:
                raise ValueError("status of one component not specified")
            if status < 0 or status > 3:
                raise ValueError(
                    "status of one component not in range 0-3 (both included)")
    if type(password) != str:
        raise TypeError("password required to be of type str.")
    elif len(password) < 8:
        raise ValueError("password too short.")
    encrypted_password = encrypt(password)
    djoined = datetime.datetime.now().isoformat(timespec="seconds")
    return json.dumps(components), encrypted_password, djoined


def encrypt(password: str):
    return sha256(bytes(password, "utf-8")).hexdigest()
