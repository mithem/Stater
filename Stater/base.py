"""
status-system of server as well as submodules
---
- 0: no errors
- 1: partially constrained
- 2: major/complete fail
- 3: offline
"""

from fileloghelper import Logger
import pymysql.cursors
from pymysql.err import OperationalError
from Stater.utils import get_server_params, encrypt
from Stater.err import *
import json

logger = Logger("base.log", "register", True, True)
logger.header(True, True, "Stater - base", 0, True, "moonshine")


def exec_sql(sql_command="SELECT * FROM tasks", verbose=True, logger: Logger = None):
    """Execute sql_command on database and return None or whatever is returned from the database. If sql_command is not specified, all tasks will get returned"""
    result = None
    if logger != None and type(logger) == Logger:
        logger.set_context("exec_sql")
    elif verbose == True:
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
    """return True if authenticated. If not, raise AuthenticationError"""
    server = get_server(name)
    if server == None:
        raise ServerNotFoundError(f"Server '{name}' not found.")
    enc_password = encrypt(password)
    if server.get("password") == enc_password:
        return True
    else:
        raise AuthenticationError(f"Cannot authenticate {name}.")


def register_server(name: str, description: str = None, repo_url: str = None, main_status: int = None, components: dict = None, password: str = None):
    """register server.
    :param name: a unique name for the server
    :param description: longer, human-readable description of the server (optional)
    :param repo_url: url to the github-repo (optional)
    :param components: dict of dicts for seperate sub-components of the server. Similar to this structure: {'some-name': {'status': 0}}
    :param password: new password to set. Cannot be reset.

    :type name: str
    :type description: str
    :type repo_url: str
    :type main_status: int
    :type components: dict
    :type password: str
    """
    logger.debug("trying to register server " + name)
    if password == None:
        raise TypeError("Password required.")
    components, password, joined = get_server_params(name=name, description=description, repo_url=repo_url,
                                                     main_status=main_status, components=components, password=password)
    keys = ["name", "password", "joined"]
    values = ["'" + name + "'", "'" + password + "'", "'" + joined + "'"]
    if description != None:
        keys.append("description")
        values.append("'" + description + "'")
    if repo_url != None:
        keys.append("repoURL")
        values.append("'" + repo_url + "'")
    if main_status != None:
        keys.append("mainStatus")
        values.append(main_status)
    if components != None:
        keys.append("components")
        values.append("'" + json.dumps(components)[1:-1] + "'")
    columns = ""
    my_values = ""
    for key in keys:
        columns += str(key) + ", "
    for value in values:
        my_values += str(value) + ", "

    columns = columns[:-2]
    my_values = my_values[:-2]
    try:
        exec_sql(
            f"INSERT INTO servers ({columns}) VALUES ({my_values});", True, logger)
    except pymysql.err.IntegrityError as e:
        if "name" in str(e):
            raise NameAlreadyUsedError(f"Name '{name}' is already used.")
        if "repoURL" in str(e):
            raise RepoURLAlreadyUsedError(
                f"repo-url '{repo_url}' is already used.")


def get_server(name: str = "", id: int = None):
    """Return already parsed (json -> dict) server dict object. If server does not exist, return None."""
    try:
        if id == None:
            result = exec_sql(
                f"SELECT * FROM servers WHERE name='{name}';", False)
        else:
            result = exec_sql(f"SELECT * FROM servers WHERE id={id};", False)
        if len(result) == 1:
            return result[0]
        else:
            return None
    except Exception as e:
        logger.handle_exception(e)
        raise e


def change_server(id: int, name: str = None, description: str = None, repo_url: str = None, main_status: int = None, components: dict = None, password: str = None):
    """Change server according to arguments"""
    try:
        logger.set_context("change_server")
        components_changed = components != None
        if get_server(id=id) == None:
            raise ServerNotFoundError(f"Server with id {id} not found")
        components, encrypted_password, djoined = get_server_params(
            name, description, repo_url, main_status, components, password)
        if name != None:
            logger.debug(f"changing name of server {id}", True)
            exec_sql(f"UPDATE servers SET name='{name}' WHERE id={id}", False)
        if description != None:
            logger.debug(f"changing description of server {id}", True)
            exec_sql(
                f"UPDATE servers SET description='{description}' WHERE id={id}", False)
        if repo_url != None:
            logger.debug(f"changing repo_url of server {id}", True)
            exec_sql(
                f"UPDATE servers SET repoURL='{repo_url}' WHERE id={id}", False)
        if main_status != None:
            logger.debug(f"changing main_status of server {id}", True)
            exec_sql(
                f"UPDATE servers SET mainStatus={main_status} WHERE id={id}", False)
        if components_changed:
            logger.debug(f"changing components of server {id}", True)
            exec_sql(
                f"UPDATE servers SET components='{json.dumps(components)[1:-1]}' WHERE id={id}", False)
        if password != None:
            logger.debug(f"changing password of server {id}", True)
            exec_sql(
                f"UPDATE servers SET password='{encrypted_password}' WHERE id={id}")
    except Exception as e:
        logger.handle_exception(e)
        raise e


def get_all_servers(order_by: str = "id", limit: int = 10):
    """return list of all servers, ordered by order_by, with a limit of limit"""
    try:
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
            if limit < 0 or limit > 50:
                raise ValueError("limit not in range 1-50 (both included)")
        else:
            raise TypeError("limit not of type int.")
        by = params[order_by]
        if limit == 0:
            sql = "SELECT * FROM servers"
        else:
            sql = f"SELECT * FROM servers ORDER BY {by} LIMIT {limit}"
        return list(exec_sql(sql, False))
    except Exception as e:
        logger.handle_exception(e)
        raise e


def delete_server(name: str = None, id: int = None):
    try:
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
        exec_sql(f"DELETE FROM servers WHERE id={id}", False)
    except Exception as e:
        logger.handle_exception(e)
        raise e


def update_server(name: str, password: str, main_status: int = None, components: dict = None):
    try:
        authenticate(name, password)
        components_where_none = components == None
        if type(components) == str:
            components = json.loads(components)
        components, _, __ = get_server_params(
            main_status=main_status, components=components)
        id = get_server(name).get("id")
        if main_status != None:
            exec_sql(
                f"UPDATE servers SET mainStatus={main_status} WHERE id={id}")
        if not components_where_none:
            exec_sql(
                f"UPDATE servers SET components='{components}' WHERE id={id}")
    except Exception as e:
        logger.handle_exception(e)
        raise e


def update_component(server_name: str, password: str, component_name: str, component_status: int):
    try:
        authenticate(server_name, password)
        server = get_server(server_name)
        server["components"] = json.loads(server["components"])
        try:
            server["components"][component_name]["status"] = component_status
        except KeyError:
            raise ComponentNotFoundError(
                f"Component '{component_name}' not found")
        exec_sql(
            f"UPDATE servers SET components='{json.dumps(server['components'])}' WHERE id={server.get('id')}")
    except Exception as e:
        logger.handle_exception(e)
        raise e
