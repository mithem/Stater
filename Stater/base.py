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
from Stater.utils import get_server_params
from Stater.err import AuthenticationError, ServerNotFoundError
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


def register_server(name: str, description: str = "", repo_url: str = "", main_status: int = 0, components: list = []):
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
    components = get_server_params(
        name, description, repo_url, main_status, components)
    exec_sql(
        f"INSERT INTO servers (name, description, repoURL, mainStatus, componentStatus) VALUES ('{name}', '{description}', '{repo_url}', {main_status}, '{components}');")


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
