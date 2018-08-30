import remoter.cmd
import example.demo


def server():
    remoter.cmd.server(example.demo.Demo)


def client():
    remoter.cmd.client(example.demo.Demo)


if __name__ == '__main__':
    server()
