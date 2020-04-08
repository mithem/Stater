import json
import os
import string

import serverly
from serverly import Request, Response, serves, logger, error_response

from Stater import base, err

address = ("localhost", 8084)

serverly.name = "StaterServer"
logger.filename = "server.log"
logger.verbose = True


serverly.register_error_response(401, "Unauthorized.", "base")
serverly.register_error_response(
    406, "Unable to parse required parameters (JSON). Expected ")
serverly.register_error_response(404, "Server not found.", "base")


@serves("GET", "/api/getserver")
def api_get_server(req: Request):
    try:
        name = req.obj.get("name", "NOTANAME")
    except AttributeError:
        name = "NOTANAME"
    if name == "NOTANAME":
        response = error_response(406, "'name'")
    else:
        try:
            req_server = base.get_server(name=name)
            if req_server != None:
                print("SERVER FOUND!")
                del req_server["password"]
                req_server["components"] = json.loads(
                    req_server["components"])
                for key, value in req_server["components"].items():
                    value["name"] = key
                response = Response(body=req_server)
            else:
                print(serverly.error_response_templates)
                response = error_response(404)
        except Exception as e:
            logger.handle_exception(e)
            response = Response(500, body=str(e))
    return response


@serves("POST", "/api/register(server)?")
def api_register_server(req: Request):
    try:
        base.register_server(req.obj["name"], req.obj.get("description", None), req.obj.get(
            "repoURL", None), req.obj.get("mainStatus", None), req.obj.get("components", None), req.obj["password"])
        create_server_details_page(base.get_server(req.obj["name"]))
        response = Response(201, body="Successfully registered server.")
    except KeyError:
        response = error_response(406, "'name'", "'password'")
    except (err.NameAlreadyUsedError, err.RepoURLAlreadyUsedError) as e:
        response = Response(406, body=str(e))
    except Exception as e:
        logger.handle_exception(e)
        response = Response(500, body=type(e).__name__ + ": " + str(e))
    return response


@serves("DELETE", "/api/delete(server)?")
def api_delete_server(req: Request):
    try:
        base.authenticate(req.obj.get("name", "notaname"),
                          req.obj.get("password", ""))
        if req.obj.get("name", None) != None:
            base.delete_server(req.obj.get("name"))
            delete_server_details_page(req.obj.get("name"))
        else:
            server = base.get_server(id=req.obj.get("id", -1))
            base.delete_server(id=server.get("id", -1))
            delete_server_details_page(server.get("name", "notaname"))
        response = Response(
            body="Deleted server successfully (just from the Stater-system :P).")
    except err.AuthenticationError:
        response = error_response(401)
    except err.ServerNotFoundError:
        response = error_response(404)
    except Exception as e:
        response = Response(
            500, body=f"Exception ({type(e).__name__}): " + str(e))
    return response


@serves("PUT", "/api/updateserver")
def api_update_status(req: Request):
    try:
        components = req.obj.get("components", None)
        print("components:", components, type(components))
        base.update_server(req.obj["name"], req.obj["password"], main_status=req.obj.get(
            "mainStatus", None), components=components)
        response = Response(body="Updated server.")
    except err.AuthenticationError:
        response = error_response(401)
    except KeyError:
        response = error_response(
            406, "'name'", "'password'", "(optional) 'components'", "(optional) 'mainStatus'")
    except Exception as e:
        response = Response(500, body=str(e))
    return response


@serves("PUT", "/api/change(server)?")
def api_change_server(req: Request):
    try:
        id = req.obj.get("id", -1)
        if id == -1:
            server = base.get_server(name=req.obj["name"])
        else:
            server = base.get_server(id=id)
        compo = req.obj.get("components", None)
        if compo != None:
            components = json.loads(compo)
        else:
            components = None
        base.authenticate(server.get("name"), req.obj["password"])
        base.change_server(server.get("id"), req.obj.get("newName", None), req.obj.get("description", None), req.obj.get(
            "repoURL", None), req.obj.get("mainStatus", None), components, req.obj.get("newPassword", None))
        response = Response(body="Changed server successfully.")
    except err.AuthenticationError:
        response = error_response(401)
    except KeyError:
        response = error_response(406, "'id'/'name'", "'password'")
    except err.ServerNotFoundError:
        response = error_response(404)
    except Exception as e:
        serverly.logger.handle_exception(e)
        response_msg = str(e)
    return response


@serves("PUT", "/api/updatecomponent")
def api_update_component(req: Request):
    try:
        base.authenticate(req.obj["name"], req.obj["password"])
        server_name = req.obj.get("serverName", req.obj["name"])
        component_name = req.obj.get(
            "component", req.obj.get("componentName", "NOTACOMPONENT"))
        status = req.obj.get("status", req.obj.get("newStatus", "NOTASTATUS"))

        if server_name == "NOTANAME" or component_name == "NOTACOMPONENT" or status == "NOTASTATUS":
            raise KeyError()

        base.update_component(
            server_name, req.obj["password"], component_name, status)
        response = Response(body="Updated component.")
    except err.AuthenticationError:
        response = error_response(401)
    except KeyError:
        response = error_response(
            406, "'name'", "'password'", "'componentName'", "'status'")
    except Exception as e:
        serverly.logger.handle_exception(e)
        response_msg = str(e)
    return response


@serverly.serves_post("/api/authenticate")
def api_authenticate(req: Request):
    try:
        base.authenticate(req.obj["name"], req.obj["password"])
        request = Request(body="Authorized.")
    except KeyError:
        response = error_response(406, "'name'", "'password'")
    except err.AuthenticationError:
        response = error_response(401)
    except err.ServerNotFoundError:
        response = error_response(404)
    except Exception as e:
        serverly.logger.handle_exception(e)
        response = Response(500, body=str(e))
    return response


def create_server_details_page(server: dict):
    name = server.get("name")
    repo_url = server.get("repoURL")
    with open("Stater/src/server_template.html", "r") as f:
        template = string.Template(f.read())
    server_detail_page_content = template.safe_substitute(
        server_name=name, json_not_parsed=json.dumps({"name": name}), server_description=server.get("description"), repo_url=str(repo_url))
    filename = "Stater/src/servers/" + str(name) + ".html"
    with open(filename, "w") as f:
        f.write(server_detail_page_content)
    serverly.static_page(filename, "/server/" + name)


def delete_server_details_page(server_name: str):
    serverly.unregister("GET", "/server/"+server_name)
    os.remove("Stater/src/servers/" + server_name + ".html")


serverly.static_page("Stater/src/dashboard.html", "/dashboard")
serverly.static_page("Stater/src/login.html", "/login")
serverly.static_page("Stater/src/register.html", "/register")


def start(superpath="/"):
    init_custom_servers()
    serverly.address = address
    serverly.start(superpath)


def init_custom_servers():
    for f in os.listdir("Stater/src/servers/"):
        os.remove("Stater/src/servers/" + f)
    for s in base.get_all_servers(limit=0):
        create_server_details_page(s)
