from core.program import MonitorProgram, check_python_existence
import asyncio
from collections import deque 

class WaveLengthMeterLock(MonitorProgram):
    def __init__(self, arg, name_mapping: list[str], unlock_threshold=1e-5) -> None:
        if check_python_existence("wlm"):
            raise RuntimeError(
                "There is already an injection lock monitor running! Shut it down before attempting to run this one.")
        super().__init__(arg)
        self.name_mapping = name_mapping
        self.errors = [deque(maxlen=50) for _ in range(len(self.name_mapping))]
        self.unlock_threshold = unlock_threshold
        self.proc: asyncio.subprocess.Process = None

    async def state_monitor(self):
        while True:
            cout = await self.proc.stdout.readline()
            message = cout.strip().decode()
            channel, error = message.split(': ')
            if int(channel) > self.name_mapping:
                raise ValueError("Too few channels in name_mapping!") 
            self.errors[int(channel)].append(float(error))
            await asyncio.sleep(0.1)

    async def wait_until_ready(self):
        await super().wait_until_ready()
        self.tsk = asyncio.create_task(self.state_monitor())
        self.proc.stdin.write(b'lock\n')
        await self.proc.stdin.drain()

    def test_precondition(self):
        def get_std(dq : deque) -> float:
            ret = 0.
            for x in dq:
                ret += x ** 2 
            ret /= 50 ** .5 
            return ret 
        return all(get_std(dq) < self.unlock_threshold  for dq in self.errors)

    async def close(self):
        self.tsk.cancel()
        self.proc.stdin.write(b'stop\n')
        await self.proc.stdin.drain()
        return await super().close()
