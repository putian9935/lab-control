''' Server daemon program 

run this program on slave machines
'''
import subprocess
import asyncio
import socket
import traceback


def check_slave_existence():
    proc = subprocess.Popen("wmic process where " + '"name like ' + "'%python%'" + '" get processid,commandline',
                            stdout=subprocess.PIPE)
    while True:
        l = proc.stdout.readline()
        if b'launch_slave' in l:
            return list(l.decode().strip().split())[-1]
        if not l:
            break
    proc.kill()
    proc.wait()


def kill_proc(pid):
    if pid is None:
        return
    subprocess.run((rf'taskkill /F /PID {pid}'))


class RPyCSlaveDaemon():
    def __init__(self, port=None):
        pid = check_slave_existence()
        if pid is not None:
            print(
                f'[INFO] Found slave running with pid {pid}. Killing it.')
            kill_proc(pid)
        if port is None:
            port = 18816
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('0.0.0.0', port))
        self.s.listen()
        self.loop = asyncio.get_event_loop()

    async def handle(self, conn, port=None):
        if port is None:
            port = 18812
        with conn:
            while True:
                data = (await self.loop.run_in_executor(None, lambda: conn.recv(100))).strip()
                if data == b'start':
                    await asyncio.subprocess.create_subprocess_shell(
                        (rf"python launch_slave.py --host 0.0.0.0 -p {port}"),
                        stdin=asyncio.subprocess.PIPE
                    )
                    conn.sendall(b'done')
                    return
                elif not len(data):
                    return

    async def serve(self):
        print('Waiting for connection...')
        task = None
        try:
            while True:
                conn, addr = await self.loop.run_in_executor(None, self.s.accept)
                conn.sendall(b'good')
                kill_proc(check_slave_existence())
                task = asyncio.create_task(self.handle(conn))
        except Exception:
            traceback.print_exc()
        except:
            traceback.print_exc()
            if not task.cancelled() and not task.done():
                task.cancel()


async def main():
    await RPyCSlaveDaemon().serve()

asyncio.run(main())
