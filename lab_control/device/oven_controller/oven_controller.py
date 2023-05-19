from ...core.program import MonitorProgram, check_existence, kill_proc
import asyncio
from functools import partial
print = partial(print, flush=True)


class OvenController(MonitorProgram):
    def __init__(self, arg, no_check=False) -> None:
        while True:
            pid = check_existence("oven")
            if pid is not None:
                print(
                    f"[WARNING] There is already an oven controller running at <Process {pid}>! Shutting it down ..")
                kill_proc(pid)
            else:
                break
        super().__init__(arg, shell=True, cout=None)
        self.oven_temp = None
        self.viewp_temp = None
        self.no_check = no_check
        self.proc: asyncio.subprocess.Process = None

    async def temp_monitor(self, f):
        while True:
            cout = await asyncio.get_running_loop().run_in_executor(None, f.readline)
            message = cout.strip()
            if 'Oven Temp' in message:
                a, b, c, d = message.split(', ')
                _, a = a.split('= ')
                _, d = d.split('= ')
                self.viewp_temp = float(a.rstrip('C').strip())
                self.oven_temp = float(d.rstrip('C').strip())

    async def wait_until_ready(self):
        async def wait_word(f, word):
            while True:
                cout = await asyncio.get_running_loop().run_in_executor(None, f.readline)
                message = cout.strip()
                if len(message):
                    if word in message:
                        return

        await super().wait_until_ready()
        await asyncio.sleep(.3)
        self.proc.stdin.write(b'heat_both\r\n\n\n')
        await self.proc.stdin.drain()
        f = open("oven_log.txt")
        await wait_word(f, 'help')
        self.tsk = asyncio.create_task(
            self.temp_monitor(f))

    def test_precondition(self):
        if self.oven_temp < 350:
            print('[ERROR] Oven temperature too low!')
            return self.no_check
        return True

    async def close(self):
        self.tsk.cancel()
        self.proc.stdin.write(b'cool_delay\r\n\n\n')
        await self.proc.stdin.drain()
        # here we don't close the background process
        # because the viewport will be cooled down two hours later
        # return await super().close()
        print('[INFO] Oven controller is running in the background')
