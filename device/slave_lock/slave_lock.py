from core.program import MonitorProgram
import asyncio
import subprocess
import shlex


def check_python_existence(substr: str):
    proc = subprocess.Popen(shlex.split("wmic process where " + '"name like ' +
                            "'%python%'" + '" get processid,commandline'), stdout=subprocess.PIPE)
    ret = False
    while True:
        l = proc.stdout.readline()
        if substr.encode() in l:
            ret = True
            break
        if not l:
            break
    return ret


class SlaveLockMonitor(MonitorProgram):
    def __init__(self, arg) -> None:
        if check_python_existence("injection"):
            raise RuntimeError(
                "There is already an injection lock monitor running! Shut it down before attempting to run this one.")
        super().__init__(arg)
        self.slave_state = [0, 0]
        self.slave_lock_state = [0, 0]
        self.proc:asyncio.subprocess.Process = None 

    async def state_monitor(self):
        while True:
            cerr = await self.proc.stdout.readline()
            message = cerr.strip().decode() 
            for i in [2, 3]:
                if message.startswith('slave%d-lock'%i):
                    if message == 'slave%d-lock: unlocked'%i:
                        self.slave_state[i-2] = 0 
                        self.slave_lock_state[i-2] = 0
                    elif 'sweep at ' in message:
                        self.slave_state[i-2] = 1 
                        self.slave_lock_state[i-2] = 0
                    elif 'lock at ' in message:
                        self.slave_state[i-2] = 2 
                        if 'current setpoint' in message or 'relocked ' in message:
                            self.slave_lock_state[i-2] = 1
                        elif 'unlock detected ' in message:
                            self.slave_lock_state[i-2] = 0
                        else:
                            print(message) 

            await asyncio.sleep(0.1)

    async def wait_until_ready(self):
        await super().wait_until_ready()
        self.tsk = asyncio.create_task(self.state_monitor())

    def test_precondition(self):
        ret = True
        for i, (state, lock_state) in enumerate(zip(self.slave_state, self.slave_lock_state)):
            if state == 0:
                ret = False
                print(f'[WARNING] Slave {i+2} is not locked! To pass the test, at least "sweep" the cavity!')
            elif state == 1:
                print(f'[WARNING] Slave {i+2} is sweeping, use your discretion!')
            else:
                if not lock_state:
                    ret = False
                    print(f'[WARNING] Slave {i+2} is unlocked!')
        return ret 

    
    async def close(self):
        self.tsk.cancel()
        return await super().close()
