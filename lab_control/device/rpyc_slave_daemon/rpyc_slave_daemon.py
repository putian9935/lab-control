from ...core.program import Target
import subprocess


class RPyCSlaveDaemon(Target):
    def __init__(self, username, addr):
        target = f'{username}@{addr}'
        print(f'[INFO] Creating daemon for {target} at {addr}')

        def check_slave_existence():
            proc = subprocess.Popen(("ssh", target, '%s' % (
                "wmic process where " + '"name like ' + "'%python%'" + '" get processid,commandline')),
                stdout=subprocess.PIPE)
            while True:
                l = proc.stdout.readline()
                if b'launch_slave' in l:
                    return list(l.decode().strip().split())[-1]
                if not l:
                    break

        def kill_slave(pid):
            subprocess.run(("ssh", target, rf'taskkill /F /PID {pid}'))
        pid = check_slave_existence()
        if pid is not None:
            print(
                f'[INFO] Found slave running on {target} with pid {pid}. Killing it.')
            kill_slave(pid)
        self.addr = addr 
        self.proc = subprocess.Popen(
            ("ssh", target, r"C:\Users\strontium_remote1\AppData\Local\Programs\Python\Python39\Python C:\Users\strontium_remote1\Desktop\launch_slave.py --host 0.0.0.0"))

    def test_precondition(self):
        if self.proc.poll is not None:
            raise SystemExit
        return True

    async def close(self):
        self.proc.kill()
        self.proc.wait()

