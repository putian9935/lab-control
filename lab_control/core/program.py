from .target import Target
import asyncio
import shlex
import subprocess
from functools import partial
print = partial(print, flush=True)


class Program(Target):
    """ Target for running external program 
    
    To make the usual program work, it is strongly advisable to put a newline character after each print statement. 

    This is especially important if the print comes from a call like input.  
    """

    def __init__(self, args, shell=False, cout=asyncio.subprocess.PIPE) -> None:
        """ args is the same as the first argument in subprocess.run """
        super().__init__()
        self.args = args
        self.proc_handle = len(type(self).backgrounds)
        if not shell:
            type(self).backgrounds.append(
                asyncio.create_subprocess_exec(
                    *shlex.split(args, posix=False),
                    stdout=cout,
                    stdin=asyncio.subprocess.PIPE))
        else:
            type(self).backgrounds.append(
                asyncio.create_subprocess_shell(
                    args,
                    stdout=cout,
                    stdin=asyncio.subprocess.PIPE))

    async def wait_until_ready(self):
        tsk = type(self).tasks[self.proc_handle]
        while not tsk.done() and not tsk.cancelled():
            await asyncio.sleep(0.01)
        if tsk.cancelled():
            raise RuntimeError(
                f"Error in building program for {type(self).__name__}!")
        self.proc: asyncio.subprocess.Process = tsk.result()
        if self.proc.returncode is not None:
            raise RuntimeError(
                f"Process {self.proc} is done with return code {self.proc.returncode}")
        print(
            f'[INFO] Running program at {self.proc} for {type(self).__name__}')


    async def close(self):
        self.proc.kill()
        await self.proc.wait()
        print(
            f'[INFO] Program {self.proc} for {type(self).__name__} closed!')


    async def write(self, stuff):
        self.proc.stdin.write(stuff)
        await self.proc.stdin.drain()

class MonitorProgram(Program):
    """ Target for running external program """

    def test_precondition(self):
        if self.proc.returncode is not None:
            raise RuntimeError(
                f"Process {self.proc} is done with return code {self.proc.returncode}")
        return True

    def test_postcondition(self):
        return self.test_precondition()


def check_existence(substr: str) -> str:
    proc = subprocess.Popen("wmic process where " + '"name like ' + "'%python%'" + '" get processid,commandline',
                            stdout=subprocess.PIPE)
    while True:
        l = proc.stdout.readline()
        if substr.encode() in l:
            return list(l.decode().strip().split())[-1]
        if not l:
            break
    proc.kill()
    proc.wait()


def kill_proc(pid: str):
    if not pid: return 
    subprocess.run((rf'taskkill /F /PID {pid}'))
    return pid


async def wait_for_prompt(cout, prompt='>>> '):
    while True:
        line = await cout.readline() 
        if prompt in line.decode():
            return 
        else:
            pass 
            # print(line.decode())
