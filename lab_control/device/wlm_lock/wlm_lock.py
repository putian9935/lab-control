from ...core.program import MonitorProgram, check_existence, kill_proc
import asyncio
from collections import deque
from typing import List
import traceback
from functools import partial
print = partial(print, flush=True)


class WaveLengthMeterLock(MonitorProgram):
    def __init__(self, arg, name_mapping: List[str], ch_mapping, unlock_threshold=1e-8) -> None:
        pid = check_existence("wlm")
        if pid is not None:
            print(
                "[WARNING] There is already an wavelength meter lock monitor running! Shutting it down.")
            kill_proc(pid)
        super().__init__(arg)
        self.name_mapping = name_mapping
        self.ch_mapping = ch_mapping
        self.errors = [deque(maxlen=50) for _ in range(len(self.name_mapping))]
        self.unlock_threshold = unlock_threshold
        self.proc: asyncio.subprocess.Process = None

    async def state_monitor(self, f):
        try:
            while True:
                cout = await asyncio.get_running_loop().run_in_executor(None, f.readline)
                message = cout.strip()
                if len(message) < 2 or message[1] != ',':
                    await asyncio.sleep(.01)
                    continue
                lst = list(message.split(', '))
                channel = int(lst[0])
                if channel not in self.ch_mapping:
                    raise ValueError("Too few channels in name_mapping!")
                err = float(lst[2])
                if len(self.errors[self.ch_mapping[channel]]) == 50:
                    self.errors[self.ch_mapping[channel]].popleft()
                self.errors[self.ch_mapping[channel]].append(err)
                await asyncio.sleep(0.01)
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
                await asyncio.sleep(.2)

        await super().wait_until_ready()
        for ch in self.ch_mapping.keys():
            open("log%d.txt" % ch, "w").close()  # clean content
        await asyncio.sleep(.2)
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
        def get_std(dq: deque) -> float:
            ret = 0.
            for x in dq:
                ret += x ** 2
            ret /= 50 ** .5
            return ret
        return all(get_std(dq) < self.unlock_threshold for dq in self.errors)

    async def close(self):
        for tsk in self.tsks:
            tsk.cancel()
        self.proc.stdin.write(b'stop\r\n\n')
        await self.proc.stdin.drain()
        return await super().close()
