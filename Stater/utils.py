import re
import json
from hashlib import sha256
import datetime


def get_server_params(name: str = None, description: str = None, repo_url: str = None, main_status: int = None, components: list = None, password: str = None):
    """check args for user errors and return components: list, as a json string"""
    if name != None and len(name) > 20:
        raise ValueError("name argument too long (max 20)")
    if not re.match("^[a-z_][a-z_.-]", name) or "#" in name:
        raise ValueError("Username invalid.")
    if description != None and len(description) > 1024:
        raise ValueError("description argument too long")
    if repo_url != None and not re.match("^https?://(www\.)?[\w.]+.\w{2,}", repo_url):
        raise ValueError("repo_url argument invalid.")
    elif repo_url != None:
        repo_url = ""
    if main_status != None and main_status < 0 and main_status > 3:
        raise ValueError("main_status argument not 0, 1, 2, or 3")
    if components != None and type(components) != list:
        raise TypeError("component_status is not a list.")
    for c in components:
        if type(c) != dict:
            raise TypeError(
                "component in component_status: list is not of type dict")
        name = c.get("name", "NOTFOUND")
        if name == "NOTFOUND":
            name = c.get("id", "NOTANAME")
            if name != "NOTANAME":
                del c["id"]
                c["name"] = name
        description = c.get("description", "NOTADESCRIPTION")
        status = c.get("status", "NOTFOUND")
        if status == "NOTFOUND":
            status = c.get("code", -1)
            if status != -1:
                del c["code"]
                c["status"] = status
        if name == "NOTANAME":
            raise ValueError("name attribute of one component not specified.")
        if type(name) != str:
            raise TypeError("name attribute of one component not of type str")
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
    if len(password) < 8:
        raise ValueError("password too short.")
    encrypted_password = encrypt(password)
    djoined = datetime.datetime.now().isoformat(timespec="seconds")
    return json.dumps(components), encrypted_password, djoined


def encrypt(password: str):
    return sha256(bytes(password, "utf-8")).hexdigest()
