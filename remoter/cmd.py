import argparse

import remoter.server
import remoter.client


def server(*cls):
    p = argparse.ArgumentParser('remoter-server')
    p.add_argument('--host', default='0.0.0.0')
    p.add_argument('--port', type=int, default=8080)
    p.add_argument('--debug', default=False, action='store_true')
    args = p.parse_args()

    srv = remoter.server.Server()

    for c in cls:
        srv.register(c)

    srv.run(host=args.host, port=args.port, debug=args.debug)


def client(cls, plr):
    p = argparse.ArgumentParser('remoter-client')
    p.add_argument('--host', default='localhost')
    p.add_argument('--port', type=int, default=8080)
    p.add_argument('--debug', default=False, action='store_true')
    p.add_argument('--game', type=int)
    p.add_argument('--as', dest='pid', type=int)
    args = p.parse_args()

    cli = remoter.client.Client(cls, plr)

    cli.run(host=args.host, port=args.port, debug=args.debug, game=args.game, pid=args.pid)


if __name__ == '__main__':
    client()
