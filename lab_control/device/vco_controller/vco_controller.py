from ...core.target import Target
from ...core.action import Action, set_pulse
from ...core.types import *
from lab_control.core.util.ts import to_plot, pulsify, merge_seq_aio, shift_list_by_one
from lab_control.core.util.loader import load_module 
from aioserial import AioSerial


def setup_port(com_port):
    ser = AioSerial(baudrate=2000000, timeout=0.05)
    ser.port = com_port
    ser.dtr = False
    return ser


class VCOController(Target):
    def __init__(self, port, ts_channel) -> None:
        """ args is the same as the first argument in subprocess.run """
        super().__init__()
        self.ts_channel = ts_channel
        self.port = port
        self.load(port)

    @Target.disable_if_offline
    @Target.load_wrapper
    def load(self, port):
        self.backend = load_module(
            'lab_control.device.vco_controller.backend',
            ser=setup_port(port)
        )

    async def wait_until_ready(self):
        await self.backend.send_trig_disable()
        self.buffer_filename = f'vco_vref_temp/{self.port}'
        open(self.buffer_filename, 'w').close()

    async def at_acq_start(self):
        # clear contents
        open(self.buffer_filename, 'w').close()
        self.backend.ser.open()

    async def at_acq_end(self):
        self.backend.ser.close()


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
        if not extras:
            await target.backend.exp_action()
            return
        contents = '\n'.join(
            f'{_dt},{_vref}'
            for _, dt, vref in merge_seq_aio(*(zip(*extras)))
            for _dt, _vref in zip(shift_list_by_one(dt), shift_list_by_one(vref))
        )
        try:
            # in case file does not exist
            if open(target.buffer_filename).read() == contents:
                # start experiment
                await target.backend.exp_action()
                return
        finally:
            pass

        #  prepare file
        with open(target.buffer_filename, 'w') as f:
            f.write(contents)
        # upload file
        from time import perf_counter
        dt = [
            _dt
            for _, dt, vref in merge_seq_aio(*(zip(*extras)))
            for _dt, _vref in zip(shift_list_by_one(dt), shift_list_by_one(vref))
        ]
        vref = [
            target.backend.detuning2DDS(_vref)
            for _, dt, vref in merge_seq_aio(*(zip(*extras)))
            for _dt, _vref in zip(shift_list_by_one(dt), shift_list_by_one(vref))
        ]
        await target.backend.set_param(dt, vref)
        # await wait_for_prompt(target.proc.stdout)
        # start experiment
        await target.backend.exp_action()

    @classmethod
    async def run_postprocess_cls(cls, target: VCOController):
        # exit from experiment
        await target.backend.stop()

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
