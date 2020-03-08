"""
status-system of server as well as submodules
---
- 0: no errors
- 1: some functionality faulty
- 2: major/complete fail
- 3: offline
"""

from fileloghelper import Logger
import pymysql.cursors
from pymysql.err import OperationalError
from Stater.utils import get_server_params, encrypt
from Stater.err import *
import json


def exec_sql(sql_command="SELECT * FROM tasks", verbose=True, logger: Logger = None):
    """Execute sql_command on database and return None or whatever is returned from the database. If sql_command is not specified, all tasks will get returned"""
    result = None
    if logger != None and type(logger) == Logger:
        logger.set_context("exec_sql")
    else:
        logger = Logger("exec_sql.log", "exec_sql", True, True)
    try:
        connection = pymysql.connect(host='localhost',
                                     user='stater_db_wrapper',
                                     password='stater_wrapper007',
                                     db='stater',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
    except OperationalError as e:
        logger.handle_exception(e)
        raise AuthenticationError("Access denied to database")
    if verbose and logger != None:
        logger.success("connected to database", False)
    if verbose and logger != None:
        logger.debug("executing SQL-Command: " + sql_command)
    with connection.cursor() as cursor:
        cursor.execute(sql_command)
        if "SELECT" in sql_command:
            result = cursor.fetchall()
        else:
            connection.commit()
    if verbose and logger != None:
        logger.debug("SQL query returned: " + str(result))
    try:
        connection.close()
        if verbose and logger != None:
            logger.success("Shut down connection to database", False)
    except Exception as e:
        if logger != None and type(logger) == Logger:
            logger.handle_exception(e)
        else:
            print(e)
    finally:
        return result


def authenticate(name: str, password: str):
    server = get_server(name)
    if server == None:
        raise ServerNotFoundError(f"Server '{name}' not found.")
    enc_password = encrypt(password)
    return server.get("password") == enc_password


def register_server(name: str, description: str = None, repo_url: str = None, main_status: int = 0, components: list = [], password: str = None):
    """register server.
    :param name: a unique name for the server
    :param description: longer, human-readable description of the server (optional)
    :param repo_url: url to the github-repo (optional)
    :param component_status: list of dicts for seperate sub-components of the server. Similar to this structure: [{'name': 'some-name', 'description': 'some description', 'status': 0}]

    :type name: str
    :type description: str
    :type repo_url: str
    :type main_status: int
    :type component_status: dict
    """
    components, password, joined = get_server_params(
        name, description, repo_url, main_status, components, password)
    try:
        exec_sql(
            f"INSERT INTO servers (name, description, repoURL, mainStatus, components, password, joined) VALUES ('{name}', '{description}', '{repo_url}', {main_status}, '{components}', '{password}', '{joined}');")
    except pymysql.err.IntegrityError as e:
        if "name" in str(e):
            raise NameAlreadyUsedError(f"Name '{name}' is already used.")
        if "repoURL" in str(e):
            raise RepoURLAlreadyUsedError(
                f"repo-url '{repo_url}' is already used.")


def get_server(name: str = "", id: int = None):
    """Return already parsed (json -> dict) server dict object. If server does not exist, return None."""
    if id == None:
        result = exec_sql(f"SELECT * FROM servers WHERE name='{name}';")
    else:
        result = exec_sql(f"SELECT * FROM servers WHERE id={id};")
    if len(result) == 1:
        return result[0]
    else:
        return None


def change_server(id: int, name: str = None, description: str = None, repo_url: str = None, main_status: int = None, components: list = []):
    """Change server according to arguments"""
    if get_server(id=id) == None:
        raise ServerNotFoundError(f"Server with id {id} not found")
    components = get_server_params()
    if name != None:
        exec_sql(f"UPDATE servers SET name='{name}' WHERE id={id}")
    if description != None:
        exec_sql(
            f"UPDATE servers SET description='{description}' WHERE id={id}")
    if repo_url != None:
        exec_sql(f"UPDATE servers SET repoURL='{repo_url}' WHERE id={id}")
    if main_status != None:
        exec_sql(
            f"UPDATE servers SET mainStatus={main_status} WHERE id={id}")
    if components != None:
        exec_sql(
            f"UPDATE servers SET components='{json.dumps(components)}' WHERE id={id}")


def get_all_servers(order_by: str = "id", limit: int = 10):
    """return list of all servers, ordered by order_by, with a limit of limit"""
    params = {
        "id": "id",
        "djoined": "joined",
        "joined": "joined",
        "name": "name",
        "status": "mainStatus",
        "main_status": "mainStatus"
    }
    if not order_by in params.keys():
        raise ValueError("'by'-parameter not valid.")
    if type(limit) == int:
        if limit < 1 or limit > 50:
            raise ValueError("limit not in range 1-50 (both included)")
    else:
        raise TypeError("limit not of type int.")
    by = params[order_by]
    return list(exec_sql(f"SELECT * FROM servers ORDER BY {by} LIMIT {limit}"))


def delete_server(name: str = None, id: int = None):
    if name != None:
        if type(name) != str:
            raise TypeError("name not of type str.")
        server = get_server(name)
    elif id != None:
        if type(id) != int:
            raise TypeError("id not of type int.")
        server = get_server(id=id)
    if server == None:
        raise ServerNotFoundError("Server not found. Could not delete.")
    id = server.get("id")
    exec_sql(f"DELETE FROM servers WHERE id={id}")
