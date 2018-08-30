import argparse

import remoter.server


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


def client(*cls):
    p = argparse.ArgumentParser('remoter-client')
    p.add_argument('--host', default='localhost')
    p.add_argument('--port', type=int, default=8080)
    p.add_argument('--debug', default=False, action='store_true')
    args = p.parse_args()

    print(args)


if __name__ == '__main__':
    client()
