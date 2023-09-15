from ...core.program import Program, wait_for_prompt
from ...core.action import Action, set_pulse
from ...core.types import *
from lab_control.core.util.ts import to_plot, pulsify, merge_seq_aio, shift_list_by_one


class CoilServo(Program):
    def __init__(self, args, ts_channel) -> None:
        """ args is the same as the first argument in subprocess.run """
        super().__init__(args)
        self.ts_channel = ts_channel

    async def wait_until_ready(self):
        await super().wait_until_ready()
        await wait_for_prompt(self.proc.stdout)

    async def close(self):
        self.proc.stdin.write(b'vref 0\n')
        await self.proc.stdin.drain()
        await wait_for_prompt(self.proc.stdout)
        return await super().close()
    

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
                    for _dt, _vref in zip(shift_list_by_one(dt), shift_list_by_one(vref))
                )
            )
        
        await target.write(b'paramVref coil_vref_temp\n')
    
        
    def to_plot(self, target: CoilServo, raw: bool, *args, **kwargs) -> plot_map:
        if raw:
            return {(target.ts_channel, self.signame, 'ramp'): to_plot(self.polarity, pulsify(self.retv[0], 0))}
        else:
            ret_data: plot_value = [0, ], [self.retv[2][-1]]
            for i, (t, dt, v) in enumerate(zip(*self.retv)):
                ret_data[0].append(t)
                ret_data[0].append(t+dt)
                ret_data[1].append(self.retv[2][i-1])
                ret_data[1].append(v)
            return {(target.ts_channel, self.signame, 'ramp'): ret_data}

