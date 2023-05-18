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
    def __init__(self, addr) -> None:
        super().__init__()
        self.addr = addr
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((addr, 18816))
        wait_for(self.s, b'good')
        print(f'[INFO] Connection to {addr} good.') 
        self.s.sendall(b'start') 
        wait_for(self.s, b'done')
        print('[INFO] Waiting slave to spawn all tasks..') 
        
    async def close(self):
        self.s.close()
