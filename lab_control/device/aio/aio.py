from lab_control.core.types import plot_map
from ...core.target import Target
from ...core.action import Action, set_pulse, ActionMeta
import importlib.util
from . import ports
from .csv_reader import tv2wfm, p2r
from ...core.types import *
from lab_control.core.util.ts import to_plot, pulsify, merge_plot_maps, merge_seq_aio
import traceback
from serial.serialutil import SerialException 

aio_ts_mapping = Dict[ActionMeta, int]


if __name__ == '__main__':
    print(merge_seq_aio([[1, 2, 3], [2, 3, 10]], [
          [10, 20, 30], [20, 30, 10]], [[1, 2, 3], [1, 2, 3]]))


class AIO(Target):
    def __init__(self, *, minpd: List[int], maxpd: List[int], ts_mapping: aio_ts_mapping, port: Optional[str] = None, **kwargs) -> None:
        super().__init__()
        if not port:
            raise ValueError(f"Must specify a port for {type(self)}")
        self.ts_mapping = ts_mapping
        self.minpd = minpd
        self.maxpd = maxpd
        self.load(port)

    @Target.disable_if_offline
    @Target.load_wrapper
    def load(self, port):
        spec = importlib.util.find_spec('lab_control.device.aio.backend')
        self.backend = importlib.util.module_from_spec(spec)
        self.backend.ser = ports.setup_arduino_port(port)
        spec.loader.exec_module(self.backend)

    @Target.disable_if_offline
    async def close(self):
        self.backend.stop()

def shift_list_by_one(l: list):
    """ Shift the last element to the front """
    return [l[-1]] + l[:-1]


def shift_vdt_by_one(retv: Tuple[list]):
    return retv[0], shift_list_by_one(retv[1]), shift_list_by_one(retv[2])


@set_pulse
@AIO.take_note
class ramp(Action):
    def __init__(self, *, channel: int, **kwargs) -> None:
        'Ramp action.\n    Changes the servo setpoint by specifying the ramp time and ramp voltage change. \n    The return value must be a tuple of three lists of the trigger start time, ramp time, and ramp voltage (in percentage, 0 means min and 1 means max).'
        self.channel = channel
        super().__init__(**kwargs)
        self.retv: Tuple[List[int], List[int], List[reals]]

    def to_time_sequencer(self, target: AIO) -> ts_map:
        if ramp not in target.ts_mapping:
            raise KeyError(f"ramp is not in ts_mapping of AIO target {target}")
        return {target.ts_mapping[ramp]: (self.retv[0], False, f'{target}.ramp_trig')}

    @classmethod
    async def run_preprocess_cls(cls, target: AIO):
        # extra waveform parameters
        extras = []
        # the channel id of the servo
        chs: List[int] = [] 
        for act in target.actions[cls]:
            extras.append(act.retv)
            chs.append(act.channel)

        # deal with ramp
        for ch, (ts, dt, v) in zip(chs, merge_seq_aio(*(zip(*extras)))):
            ts, dt, v = shift_vdt_by_one((ts, dt, v))
            target.backend.ref(
                ch,
                tv2wfm(dt, p2r(v, target.maxpd[ch], target.minpd[ch])))

    def __eq__(self, __value: object) -> bool:
        return super().__eq__(__value) and self.channel == __value.channel

    def to_plot(self, target: AIO, raw: bool, *args, **kwargs) -> plot_map:
        if raw:
            return {(target.ts_mapping[ramp], self.signame, 'ramp'): to_plot(self.polarity, pulsify(self.retv[0], 0))}
        else:
            ret_data: plot_value = [0, ], [self.retv[2][-1]]
            for i, (t, dt, v) in enumerate(zip(*self.retv)):
                ret_data[0].append(t)
                ret_data[0].append(t+dt)
                ret_data[1].append(self.retv[2][i-1])
                ret_data[1].append(v)
            return {(target.ts_mapping[ramp], self.signame, 'ramp'): ret_data}


@AIO.take_note
class hsp(Action):
    def __init__(self, *, channel: int, **kwargs) -> None:
        '''Hold setpoint action.
        When the pin 35 is pulled high, the output of the corresponding channel immediately changes to the number set in hsp.
        The return value must be a pair of lists: 
        - list1: time of the transition edges of the TTL signal.
        - list2: the output DAC number corresponding to this TTL signal. 

        For instance, a return value of [1000, 2000], [500] means the DAC output is 500 between 1000 and 2000   
        '''
        self.channel = channel
        super().__init__(**kwargs)

    async def run_preprocess(self, target: AIO):
        if hsp not in target.ts_mapping:
            raise KeyError(f"hsp is not in ts_mapping of AIO target {target}")
        target.backend.hsp(
            self.channel,
            tv2wfm([1] * len(self.retv[1]), shift_list_by_one(self.retv[1])))

    def to_time_sequencer(self, target: AIO) -> ts_map:
        if hsp not in target.ts_mapping:
            raise KeyError("hsp is not in ts_mapping of AIO target")
        return {target.ts_mapping[hsp]: (self.retv[0], self.polarity, f'{target}.hsp')}

    def to_plot(self, target: AIO, raw: bool, *args, **kwargs) -> plot_map:
        x, y = to_plot(self.polarity, self.retv[0])
        # if not raw:
        #     y = [_ * self.hsp for _ in y]
        return {(target.ts_mapping[hsp], self.signame, 'hsp'): (x, y)}

    def __eq__(self, __value: object) -> bool:
        return super().__eq__(__value) and self.channel == __value.channel


if __name__ == '__main__':
    import numpy as np
    aio = AIO(
        port='COM9',
        minpd=np.array([0, 0, 0, 0]),
        maxpd=np.array([0, 0, 0, 0]),
        ts_mapping={ramp: 0, hsp: 2}
    )

    @aio(ramp, channel=0)
    def a():
        return [1000, 2000], [2, 3], [4, 5]

    @aio(ramp, channel=2)
    def a():
        return [2000, 40000], [4, 5, ], [5, 6]

    @aio(hsp, channel=0, hsp=20, polarity=True)
    def a():
        return [1, 2]
