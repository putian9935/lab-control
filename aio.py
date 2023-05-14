from target import Target
from action import Action, set_pulse
import asyncio
import importlib.util
import aio_backend.ports
from aio_backend.csv_reader import tv2wfm, p2r

class AIO(Target):
    def __init__(self, *, minpd, maxpd, ts_mapping, port=None, **kwargs) -> None:
        super().__init__()
        if not port:
            raise ValueError(f"Must specify a port for {type(self)}")
        spec = importlib.util.find_spec('.backend', 'aio_backend')
        self.backend = importlib.util.module_from_spec(spec)
        self.backend.ser = aio_backend.ports.setup_arduino_port(port)
        spec.loader.exec_module(self.backend)
        self.ts_mapping = ts_mapping
        self.minpd = minpd
        self.maxpd = maxpd

def shift_list_by_one(l : list):
    return [l[-1]] + l[:-1]
def shift_vdt_by_one(retv : tuple[list]):
    return retv[0], shift_list_by_one(retv[1]), shift_list_by_one(retv[2])

@set_pulse
@AIO.take_note
class ramp(Action):
    def __init__(self, *, channel, **kwargs) -> None:
        self.channel = channel
        super().__init__(**kwargs)

    def to_time_sequencer(self, target: AIO):
        if ramp not in target.ts_mapping:
            raise KeyError("ramp is not in ts_mapping of AIO target") 
        return {target.ts_mapping[ramp]: (self.retv[0], False, f'{target}.ramp_trig')}

    @classmethod
    async def run_prerequisite_cls(cls, target: AIO):
        extras = []
        chs = []
        for act in target.actions[cls]:
            extras.append(act.retv)
            chs.append(act.channel)

        from merge_seq_aio import merge_seq_aio
        # deal with ramp
        for ch, (ts, dt, v) in zip(chs, merge_seq_aio(*(zip(*extras)))):
            ts, dt, v = shift_vdt_by_one((ts, dt, v))
            target.backend.ref(
                ch,
                tv2wfm(dt, p2r(v, target.maxpd[ch], target.minpd[ch])))


@AIO.take_note
class hsp(Action):
    def __init__(self, *, channel, hsp, **kwargs) -> None:
        self.channel = channel
        self.hsp = hsp
        super().__init__(**kwargs)

    async def run_prerequisite(self, target: AIO):
        target.backend.hsp(self.channel, self.hsp)

    def to_time_sequencer(self, target: AIO) -> tuple[dict[int, list[int]], bool]:
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

    async def main0():
        await aio.run_prerequisite()
        await asyncio.sleep(1)
        await aio.run_prerequisite()
        await asyncio.sleep(1)

        aio.close()

    async def main():
        print(ramp.pulse, hsp.pulse)
        await aio.run_prerequisite()
        print(aio.to_time_sequencer())
        aio.close()

    asyncio.run(main())
