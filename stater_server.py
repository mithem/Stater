from Stater import server
import argparse

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--hostname", "-host", type=str, default="localhost")
    p.add_argument("--port", "-p", type=int, default=8084)
    p.add_argument("--superpath", "--path", type=str, default="/")
    args = p.parse_args()
    server.address = (args.hostname, args.port)
    server.start(args.superpath)
