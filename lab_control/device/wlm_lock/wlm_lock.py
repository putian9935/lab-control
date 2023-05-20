from ...core.program import MonitorProgram, check_existence, kill_proc
import asyncio
from .json_load import load_settings
from collections import deque
import os
import traceback
import shlex
from functools import partial
print = partial(print, flush=True)


class WaveLengthMeterLock(MonitorProgram):
    def __init__(self, arg, unlock_threshold=1e-8) -> None:
        pid = check_existence("wlm")
        if pid is not None:
            print(
                "[WARNING] There is already an wavelength meter lock monitor running! Shutting it down.")
            kill_proc(pid)
        dirname = os.path.dirname(__file__)
        fname = os.path.join(dirname, 'wlm.json')
        self.lasers = load_settings(fname)
        super().__init__(shlex.join(arg, fname), cout=asyncio.subprocess.DEVNULL)
        self.ch_mapping = {l['WaveMeterChannel']: i for i, l in enumerate(self.lasers)}
        self.errors = [deque(maxlen=50) for _ in range(len(self.lasers))]
        self.unlock_threshold = unlock_threshold
        self.proc: asyncio.subprocess.Process = None

    async def state_monitor(self, f):
        try:
            while True:
                cout = await asyncio.get_running_loop().run_in_executor(None, f.readline)
                message = cout.strip()
                if len(message) < 2 or message[1] != ',':
                    continue
                lst = list(message.split(', '))
                channel = int(lst[0])
                err = float(lst[2])
                idx = self.ch_mapping[channel]
                if len(self.errors[idx]) == 50:
                    self.errors[idx].popleft()
                self.errors[idx].append(err)
        except Exception as e:
            traceback.print_exc()
            raise e

    async def wait_until_ready(self):
        async def wait_file(f):
            while True:
                cout = await asyncio.get_running_loop().run_in_executor(None, f.readline)
                message = cout.strip()
                if len(message):
                    return

        await super().wait_until_ready()
        for ch in self.ch_mapping.keys():
            open("log%d.txt" % ch, "w").close()  # clean content
        self.proc.stdin.write(b'lock\r\n\n')
        await self.proc.stdin.drain()
        self.tsks = []
        for ch in self.ch_mapping.keys():
            f = open("log%d.txt" % ch)
            await wait_file(f)
            self.tsks.append(
                asyncio.create_task(
                    self.state_monitor(f)))  # clean content

    def test_precondition(self):
        if not super().test_precondition():
            return False

        def get_std(dq: deque) -> float:
            ret = 0.
            for x in dq:
                ret += x ** 2
            ret /= 50 ** .5
            return ret

        ret = True 
        for i, dq in enumerate(self.errors):
            if get_std(dq) > self.unlock_threshold:
                ret = False 
                print(f'[ERROR] Laser %s at wavemeter channel %d is unlocked!'(self.lasers[i]['Name'], self.lasers[i]['WaveMeterChannel']))
        return ret 

    async def close(self):
        for tsk in self.tsks:
            tsk.cancel()
        self.proc.stdin.write(b'stop\r\n\n')
        await self.proc.stdin.drain()
        return await super().close()
