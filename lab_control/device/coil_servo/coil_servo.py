from ...core.program import Program
from ...core.action import Action, set_pulse
from ...core.types import *
import asyncio
# import shlex

async def wait_for_prompt(cout, prompt='>>> '):
    while True:
        line = await cout.readline() 
        if line.decode().startswith(prompt):
            return 
        else:
            pass 
            # print(line.decode())

class CoilServo(Program):
    def __init__(self, ts_channel) -> None:
        """ args is the same as the first argument in subprocess.run """
        super().__init__(r'python Q:\indium\software\experimental_control_v2\ad5764_io\coil_vref\coil_vref_terminal_v6.py --non-interactive')
        self.ts_channel = ts_channel

    async def wait_until_ready(self):
        await super().wait_until_ready()
        await wait_for_prompt(self.proc.stdout)

    async def close(self):
        self.proc.stdin.write(b'vref 0\n')
        await self.proc.stdin.drain()
        await wait_for_prompt(self.proc.stdout)
        return await super().close()
    

def merge_seq_aio(ts: List[List[int]] = None, dts: List[list] = None, dvs: List[list] = None):
    ret = []
    if ts is None or not len(ts):
        return ret
    full_sequence = sorted(set(t for seq in ts for t in seq))
    for t, dt, dv in zip(ts, dts, dvs):
        inv_t = {v: k for k, v in enumerate(t)}
        new_dt, new_dv = [], []
        for tt in full_sequence:
            if tt in inv_t:
                new_dt.append(dt[inv_t[tt]])
                new_dv.append(dv[inv_t[tt]])
            else:
                if len(new_dv):
                    new_dv.append(new_dv[-1])
                else:
                    new_dv.append(dv[-1])
                new_dt.append(1)
        ret.append((list(full_sequence), new_dt, new_dv))
    return ret

@CoilServo.set_default
@set_pulse
@CoilServo.take_note
class ramp(Action):
    def __init__(self, **kwargs) -> None:
        'Ramp action.\n  First number is the standby value'
        super().__init__(**kwargs)

    def to_time_sequencer(self, target: CoilServo) -> ts_map:
        return {target.ts_channel: (self.retv[0], False, f'{target}.ramp_trig')}

    @classmethod
    async def run_preprocess_cls(cls, target: CoilServo):
        extras = []
        for act in target.actions[cls]:
            extras.append(act.retv)

        # deal with ramp
        
        with open('coil_vref_temp', 'w') as f:
            f.write(
                '\n'.join(
                    f'{_dt}, {_vref}' 
                    for _, dt, vref in merge_seq_aio(*(zip(*extras)))
                    for _dt, _vref in zip(dt, vref)
                )
            )
        
        await target.write(b'paramVref coil_vref_temp\n')
        