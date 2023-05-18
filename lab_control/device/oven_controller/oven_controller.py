from ...core.program import MonitorProgram, check_existence, kill_proc
import asyncio
from collections import deque
from typing import List
import traceback
from functools import partial
print = partial(print, flush=True)


class OvenController(MonitorProgram):
    def __init__(self, arg) -> None:
        pid = check_existence("oven")
        if pid is not None:
            print(
                "[WARNING] There is already an oven controller running! Shut it down before attempting to run this one.")
            kill_proc(pid)
        super().__init__(arg)
        self.oven_temp = None
        self.viewp_temp = None
        self.proc: asyncio.subprocess.Process = None

    async def temp_monitor(self, f):
        pass 

    async def wait_until_ready(self):
        async def wait_file(f):
            while True:
                cout = await asyncio.get_running_loop().run_in_executor(None, f.readline)
                message = cout.strip()
                if len(message):
                    return
                await asyncio.sleep(.2)

        await super().wait_until_ready()
        for ch in self.ch_mapping.keys():
            open("oven_log.txt" % ch, "w").close()  # clean content
        await asyncio.sleep(.2)
        self.proc.stdin.write(b'lock\r\n\n')
        await self.proc.stdin.drain()
        self.tsk
        f = open("oven_log.txt" % ch)
        await wait_file(f)
        self.tsk= asyncio.create_task(
                self.temp_monitor(f))

    def test_precondition(self):
        return True

    async def close(self):    
        self.tsk.cancel()
        self.proc.stdin.write(b'cool_delay\r\n\n')
        await self.proc.stdin.drain()
        # return await super().close()
        print('[INFO] Monitor program for oven controller is running in the background')
