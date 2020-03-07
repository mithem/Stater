import serverly
import json
from Stater import base

serverly.address = ("localhost", 8084)
serverly.name = "StaterServer"
serverly.logger.filename = "server.log"


@serverly.serves_post("/api/getserver")
def api_get_server(data):
    response_code = 200
    response_msg = ""
    print(data)
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
    return {"code": response_code}, response_msg


def start():
    serverly.start()
