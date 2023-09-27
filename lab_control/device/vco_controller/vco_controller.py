from ...core.program import Program, wait_for_prompt
from ...core.action import Action, set_pulse
from ...core.types import *
from lab_control.core.util.ts import to_plot, pulsify, merge_seq_aio, shift_list_by_one


class VCOController(Program):
    def __init__(self, args, ts_channel) -> None:
        """ args is the same as the first argument in subprocess.run """
        super().__init__(args)
        self.ts_channel = ts_channel

    async def wait_until_ready(self):
        await super().wait_until_ready()
        await wait_for_prompt(self.proc.stdout)

    async def at_acq_start(self):
        # clear contents
        open('vco_vref_temp', 'w').close()


@VCOController.set_default
@set_pulse
@VCOController.take_note
class ramp(Action):
    def __init__(self, **kwargs) -> None:
        'Ramp action.\n  First number is the standby value'
        super().__init__(**kwargs)

    def to_time_sequencer(self, target: VCOController) -> ts_map:
        return {target.ts_channel: (self.retv[0], False, f'{target}.ramp_trig')}

    @classmethod
    async def run_preprocess_cls(cls, target: VCOController):
        extras = []
        for act in target.actions[cls]:
            extras.append(act.retv)

        contents = '\n'.join(
            f'{_dt},{_vref}'
            for _, dt, vref in merge_seq_aio(*(zip(*extras)))
            for _dt, _vref in zip(dt, shift_list_by_one(vref))
        )
        try:
            # in case file does not exist
            if open('vco_vref_temp').read() == contents:
                # start experiment
                await target.write(b'exp\n')
                await wait_for_prompt(target.proc.stdout)
                return
        finally:
            pass

        #  prepare file
        with open('vco_vref_temp', 'w') as f:
            f.write(contents)
        # upload file
        await target.write(b'paramDet vco_vref_temp\n')
        await wait_for_prompt(target.proc.stdout)
        # start experiment
        await target.write(b'exp\n')
        await wait_for_prompt(target.proc.stdout)

    @classmethod
    async def run_postprocess_cls(cls, target: VCOController):
        # exit from experiment
        await target.write(b'e\n')
        await wait_for_prompt(target.proc.stdout)

    def to_plot(self, target: VCOController, raw: bool, *args, **kwargs) -> plot_map:
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
