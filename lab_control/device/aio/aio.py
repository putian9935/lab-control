from ...core.target import Target
from ...core.action import Action, set_pulse, ActionMeta
import importlib.util
from . import ports
from .csv_reader import tv2wfm, p2r
from typing import List, Tuple, Dict, Optional
from ...core.types import *

aio_ts_mapping = Dict[ActionMeta, int]


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


if __name__ == '__main__':
    print(merge_seq_aio([[1, 2, 3], [2, 3, 10]], [
          [10, 20, 30], [20, 30, 10]], [[1, 2, 3], [1, 2, 3]]))


class AIO(Target):
    def __init__(self, *, minpd: List[int], maxpd: List[int], ts_mapping: aio_ts_mapping, port: Optional[str] = None, **kwargs) -> None:
        super().__init__()
        if not port:
            raise ValueError(f"Must specify a port for {type(self)}")
        spec = importlib.util.find_spec('lab_control.device.aio.backend')
        self.backend = importlib.util.module_from_spec(spec)
        self.backend.ser = ports.setup_arduino_port(port)
        spec.loader.exec_module(self.backend)
        self.ts_mapping = ts_mapping
        self.minpd = minpd
        self.maxpd = maxpd


def shift_list_by_one(l: list):
    """ Shift the last element to the front """
    return [l[-1]] + l[:-1]


def shift_vdt_by_one(retv: Tuple[list]):
    return retv[0], shift_list_by_one(retv[1]), shift_list_by_one(retv[2])


@set_pulse
@AIO.take_note
class ramp(Action):
    def __init__(self, *, channel: int, **kwargs) -> None:
        'Ramp action.\n    Changes the servo setpoint by specifying the ramp time and ramp voltage change. \n    The return value must be a tuple of three lists of the trigger start time, ramp time, and ramp voltage change.'
        super().__init__(**kwargs)
        self.channel = channel

    def to_time_sequencer(self, target: AIO) -> ts_map:
        if ramp not in target.ts_mapping:
            raise KeyError(f"ramp is not in ts_mapping of AIO target {target}")
        return {target.ts_mapping[ramp]: (self.retv[0], False, f'{target}.ramp_trig')}

    @classmethod
    async def run_preprocess_cls(cls, target: AIO):
        extras = []
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


@AIO.take_note
class hsp(ramp):
    def __init__(self, *, channel: int, hsp: int, **kwargs) -> None:
        'Hold setpoint action.\n    When the pin 35 is pulled high, the output of the corresponding channel immediately changes to the number set in hsp.\n    The return value must be a list of time for the transition edges of the TTL signal. '
        super().__init__(channel=channel, **kwargs)
        self.hsp = hsp

    async def run_preprocess(self, target: AIO):
        if hsp not in target.ts_mapping:
            raise KeyError(f"hsp is not in ts_mapping of AIO target {target}")
        target.backend.hsp(self.channel, self.hsp)

    def to_time_sequencer(self, target: AIO) -> ts_map:
        if hsp not in target.ts_mapping:
            raise KeyError("hsp is not in ts_mapping of AIO target")
        return {target.ts_mapping[hsp]: (self.retv, self.polarity, f'{target}.hsp')}


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
