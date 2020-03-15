import json
import os
import string

import serverly

from Stater import base, err

address = ("localhost", 8084)

serverly.name = "StaterServer"
serverly.logger.filename = "server.log"


@serverly.serves_post("/api/getserver")
def api_get_server(data):
    response_code = 200
    response_msg = ""
    try:
        name = data.get("name", "NOTANAME")
        print("name:", name)
    except AttributeError:
        name = "NOTANAME"
    if name == "NOTANAME":
        response_code = 406
        response_msg = "Please include the name of the server you want to get data for."
    else:
        server_data = base.get_server(name=name)
        server_data["components"] = json.loads(server_data["components"])
        for key, value in server_data["components"].items():
            value["name"] = key
        response_msg = json.dumps(server_data)
    return {"response_code": response_code, "Content-type": "application/json"}, response_msg


@serverly.serves_post("/api/register(server)?")
def api_register_server(data):
    response_code = 200
    response_msg = "error"
    try:
        base.register_server(data["name"], data.get("description", None), data.get(
            "repoURL", None), data.get("mainStatus", None), data.get("components", None), data["password"])
        create_server_details_page(base.get_server(data["name"]))
        response_code = 200
        response_msg = "Registered successfully"
    except KeyError:
        response_msg = "Unable to parse required parameters. Expected at least 'name' and 'password'. Please refer to the docs."
    except (err.NameAlreadyUsedError, err.RepoURLAlreadyUsedError) as e:
        response_code = 406
        response_msg = str(e)
    except Exception as e:
        serverly.logger.handle_exception(e)
        response_code = 500
        response_msg = str(e)
    return {"response_code": response_code, "Content-type": "text/plain"}, response_msg


@serverly.serves_post("/api/delete(server)?")
def api_delete_server(data):
    response_code = 500
    response_msg = "error"
    try:
        base.authenticate(data.get("name", "notaname"),
                          data.get("password", ""))
        if data.get("name", None) != None:
            base.delete_server(data.get("name"))
            delete_server_details_page(data.get("name"))
        else:
            server = base.get_server(id=data.get("id", -1))
            base.delete_server(id=server.get("id", -1))
            delete_server_details_page(server.get("name", "notaname"))
        response_code = 200
        response_msg = "Deleted server successfully (just from the Stater-system :P)."
    except err.AuthenticationError:
        response_code = 401
        response_msg = "Unauthorized."
    except Exception as e:
        response_code = 406
        response_msg = str(e)
    return {"response_code": response_code, "Content-type": "text/plain"}, response_msg


@serverly.serves_post("/api/updateserver")
def api_update_status(data):
    response_code = 500
    response_msg = "error"
    try:
        components = data.get("components", None)
        print("components:", components, type(components))
        base.update_server(data["name"], data["password"], main_status=data.get(
            "mainStatus", None), components=components)
        response_code = 200
        response_msg = "Updated server."
    except err.AuthenticationError:
        response_code = 401
        response_msg = "Unauthorized"
    except KeyError:
        response_code = 406
        response_msg = "Unable to parse required parameters. Expected 'name', 'password' and optionally 'mainStatus' and/or 'components'"
    except Exception as e:
        response_msg = str(e)
    return {"response_code": response_code, "Content-type": "text/plain"}, response_msg


@serverly.serves_post("/api/change(server)?")
def api_change_server(data):
    response_code = 500
    response_msg = "error"
    try:
        identifier = data.get("id", base.get_server(
            data["name"]).get("id", None))
        if type(identifier) == int:
            server = base.get_server(id=identifier)
        elif type(identifier) == str:
            server = base.get_server(identifier)
        elif identifier == None:
            raise err.ServerNotFoundError()
        else:
            response_code = 406
            response_msg = "Parameter name or id of invalid type."
            server = {}
        compo = data.get("components", None)
        if compo != None:
            components = json.loads(compo)
        else:
            components = None
        base.authenticate(server.get("name"), data["password"])
        base.change_server(server.get("id"), data.get("newName", None), data.get("description", None), data.get(
            "repoURL", None), data.get("mainStatus", None), components, data.get("newPassword", None))
        response_code = 200
        response_msg = "Changed server successfully."
    except err.AuthenticationError:
        response_code = 401
        response_msg = "Unauthorized."
    except KeyError:
        response_code = 406
        response_msg = "Invalid parameters. Expected at least 'id'/'name' and 'password'"
    except err.ServerNotFoundError:
        response_code = 406
        response_msg = "Server not found."
    except Exception as e:
        serverly.logger.handle_exception(e)
        response_msg = str(e)
    return {"response_code": response_code, "Content-type": "text/plain"}, response_msg


@serverly.serves_post("/api/updatecomponent")
def api_update_component(data):
    response_code = 500
    response_msg = "error"
    try:
        base.authenticate(data["name"], data["password"])
        server_name = data.get("serverName", data["name"])
        component_name = data.get(
            "component", data.get("componentName", "NOTACOMPONENT"))
        status = data.get("status", data.get("newStatus", "NOTASTATUS"))

        if server_name == "NOTANAME" or component_name == "NOTACOMPONENT" or status == "NOTASTATUS":
            raise KeyError()

        base.update_component(
            server_name, data["password"], component_name, status)
        response_code = 200
        response_msg = "Updated component."
    except err.AuthenticationError:
        response_code = 401
        response_msg = "Unauthorized."
    except KeyError:
        response_code = 406
        response_msg = "Unable to parse required parameters. Expected 'name', 'password', 'componentName' and 'status'"
    except Exception as e:
        serverly.logger.handle_exception(e)
        response_msg = str(e)
    return {"response_code": response_code, "Content-type": "text/plain"}, response_msg


@serverly.serves_post("/api/authenticate")
def api_authenticate(data):
    response_code = 500
    response_msg = "error"
    try:
        a = base.authenticate(data["name"], data["password"])
        if a:
            response_code = 200
            response_msg = "Authorized."
        else:
            response_code = 401
            response_msg = "Unauthorized."
    except KeyError:
        response_code = 406
        response_msg = "Unable to parse required parameters 'name' and 'password'.x"
    except Exception as e:
        response_code = 500
        response_msg = str(e)
    return {"response_code": response_code, "Content-type": "text/plain"}, response_msg


def create_server_details_page(server: dict):
    name = server.get("name")
    repo_url = server.get("repoURL")
    with open("Stater/src/server_template.html", "r") as f:
        template = string.Template(f.read())
    server_detail_page_content = template.safe_substitute(
        server_name=name, json_not_parsed=json.dumps({"name": name}), server_description=server.get("description"), repo_url="<a href='" + str(repo_url) + "' target='_blank'>" + str(repo_url) + "</a>")
    filename = "Stater/src/servers/" + str(name) + ".html"
    with open(filename, "w") as f:
        f.write(server_detail_page_content)
    serverly.static_page(filename, "/server/" + name)


def delete_server_details_page(server_name: str):
    serverly.unregister("GET", "/server/"+server_name)
    os.remove("Stater/src/servers/" + server_name + ".html")


serverly.static_page("Stater/src/dashboard.html", "/dashboard")


def start(superpath="/"):
    init_custom_servers()
    serverly.address = address
    serverly.start(superpath)


def init_custom_servers():
    for f in os.listdir("Stater/src/servers/"):
        os.remove("Stater/src/servers/" + f)
    for s in base.get_all_servers(limit=0):
        create_server_details_page(s)
