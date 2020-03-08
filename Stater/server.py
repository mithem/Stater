import serverly
import json
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
        response_msg = json.dumps(server_data)
    return {"response_code": response_code}, response_msg


@serverly.serves_post("/api/register")
def api_register_server(data):
    response_code = 500
    response_msg = "error"
    try:
        base.register_server(data["name"], data.get("description", ""), data.get(
            "repoURL", None), data.get("mainStatus", 0), data.get("components", []), data["password"])
        response_code = 200
        response_msg = "Registered successfully"
    except KeyError:
        response_msg = "Unable to parse required parameters. Expected at least 'name' and 'password'. Please refer to the docs."
    except (err.NameAlreadyUsedError, err.RepoURLAlreadyUsedError) as e:
        response_code = 406
        response_msg = str(e)
    return {"response_code": response_code}, response_msg


@serverly.serves_post("/api/delete")
def api_delete_server(data):
    response_code = 500
    response_msg = "error"
    try:
        if not base.authenticate(data.get("name", "notaname"), data.get("password", "")):
            response_code = 401
            response_msg = "Unauthorized."
        else:
            base.delete_server(data.get("name", None), data.get("id", None))
            response_code = 200
            response_msg = "Deleted server successfully (just from the Stater-system)."
    except Exception as e:
        response_code = 406
        response_msg = str(e)
    return {"response_code": response_code}, response_msg


def start():
    serverly.address = address
    serverly.start()
