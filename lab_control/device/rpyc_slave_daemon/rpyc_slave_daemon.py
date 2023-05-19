from ...core.target import Target
import socket
import time


def wait_for(sock, word):
    while True:
        data = sock.recv(1024).strip()
        if len(data) == 0:
            time.sleep(1)
        elif data == word:
            break
        else:
            print(data)


class RPyCSlaveDaemon(Target):
    def __init__(self, addr, port=None) -> None:
        super().__init__()
        if port is None:
            port = 18816
        self.addr = addr
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(.8)
        try:
            self.s.connect((addr, port))
        except socket.timeout as e:
            raise socket.timeout(
                f'Cannot connect to daemon running at {addr}:{port}. Did you forget to launch the daemon?') from e
        wait_for(self.s, b'good')
        print(f'[INFO] Connection to {addr}:{port} good.')
        self.s.sendall(b'start')
        wait_for(self.s, b'done')

    async def close(self):
        self.s.close()
