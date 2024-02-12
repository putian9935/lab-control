from lab_control.core.types import plot_map
from ...core.target import Target
from ...core.action import Action, set_pulse, ActionMeta
from . import aio_ports
from .csv_reader import tv2wfm, p2r
from ...core.types import *
from lab_control.core.util.ts import to_plot, pulsify, merge_plot_maps, merge_seq_aio, shift_list_by_one
from lab_control.core.util.loader import load_module 
from functools import wraps 

import logging 
logger = logging.getLogger('device.aio')
logger.setLevel(logging.INFO)

from lab_control.core.util.profiler import measure_time
aio_ts_mapping = Dict[ActionMeta, int]
import asyncio
class AIO(Target):
    def __init__(self, *, minpd: List[int], maxpd: List[int], ts_mapping: aio_ts_mapping, port: Optional[str] = None, **kwargs) -> None:
        super().__init__()
        if not port:
            raise ValueError(f"Must specify a port for {type(self)}")
        self.ts_mapping = ts_mapping
        self.minpd = minpd
        self.maxpd = maxpd
        self.port = port 
        self.load(port)

    @Target.disable_if_offline
    @Target.load_wrapper
    def load(self, port):
        self.backend = load_module(
            'lab_control.device.aio.aio_backend',
            ser=aio_ports.setup_arduino_port(port)
        )

    @Target.disable_if_offline
    async def close(self):
        while not self.backend.ser.is_open:
            try:
                self.backend.ser.open()
            except:
                logger.error(f'Dead serial {self.__name__}')
                from subprocess import run 
                run(rf'C:\Program Files (x86)\TyTools\tycmd.exe reset --board "@{self.port}"')
        await self.backend.stop()
        self.backend.ser.close()
        
    async def at_acq_start(self):
        while not self.backend.ser.is_open:
            try:
                self.backend.ser.open()
            except:
                logger.error(f'Dead serial {self.__name__}')
                from subprocess import run 
                run(rf'C:\Program Files (x86)\TyTools\tycmd.exe reset --board "@{self.port}"')
        return await super().at_acq_start()
    
    async def at_acq_end(self):
        self.backend.ser.close()
        return await super().at_acq_end()

def shift_vdt_by_one(retv: Tuple[list]):
    return retv[0], shift_list_by_one(retv[1]), shift_list_by_one(retv[2])

def is_equal_reference(ref_a, ref_b): 
    """ compare if two references are equal """
    if len(ref_a) != len(ref_b):
        return False 
    for act_a, act_b in zip(ref_a, ref_b):
        if act_a.retv[1] != act_b.retv[1] or act_a.retv[2] != act_b.retv[2]:
            return False 
    return True 
 
def cache_cls_actions(coro_func):
    ''' stop uploading if the parameter is the same 
    
    Applies for "_cls" suffixed (i.e., classmethod decorated) coroutine functions
    '''
    @wraps(coro_func)
    async def ret(cls, target):
        if target in cls.last_target_actions:
            logger.debug(f'<{target}>: {is_equal_reference(cls.last_target_actions[target], target.actions[cls])}')
            logger.debug(f'<{target}>: {cls.last_target_actions}')
            logger.debug(f'<{target}>: {target.actions[cls]}')
            if is_equal_reference(cls.last_target_actions[target], target.actions[cls]):
                return
        cls.last_target_actions[target] = target.actions[cls]
        await coro_func(cls, target) 
    return ret 

def cache_actions(coro_func):
    ''' stop uploading if the parameter is the same '''
    @wraps(coro_func)
    async def ret(self, target):
        cls = type(self)
        if target in cls.last_target_actions:
            if self in cls.last_target_actions[target] :
                return
            else:                
                cls.last_target_actions[target].append(self)
        else:
            cls.last_target_actions[target]= [self]
        await coro_func(self, target) 
    return ret 

@set_pulse
@AIO.take_note
class ramp(Action):
    '''Ramp action 

    Changes the servo setpoint by specifying the ramp time and ramp voltage change.

    The return value must be a tuple of three lists of the trigger start time, ramp time, and ramp voltage (in percentage, 0 means min and 1 means max).
    '''

    def __init__(self, *, channel: int, **kwargs) -> None:
        self.channel = channel
        super().__init__(**kwargs)
        self.retv: Tuple[List[int], List[int], List[reals]]

    def to_time_sequencer(self, target: AIO) -> ts_map:
        if ramp not in target.ts_mapping:
            raise KeyError(f"ramp is not in ts_mapping of AIO target {target}")
        return {target.ts_mapping[ramp]: (self.retv[0], False, f'{target}.ramp_trig')}

    @classmethod
    @cache_cls_actions
    async def run_preprocess_cls(cls, target: AIO):
        # extra waveform parameters
        extras = []
        # the channel id of the servo
        chs: List[int] = []
        for act in target.actions[cls]:
            extras.append(act.retv)
            chs.append(act.channel)
        # empty actions
        if not chs:
            return  
        logger.debug(f'{target}')
        logger.debug(extras)
        logger.debug(chs)
        # deal with ramp
        for ch, (ts, dt, v) in zip(chs, merge_seq_aio(*(zip(*extras)))):
            ts, dt, v = shift_vdt_by_one((ts, dt, v))
            await target.backend.ref(
                ch,
                tv2wfm(dt, p2r(v, target.maxpd[ch], target.minpd[ch])))

    def __eq__(self, __value: object) -> bool:
        return super().__eq__(__value) and self.channel == __value.channel

    def weak_equal(self, __value: object) -> bool:
        return super().weak_equal(__value) and self.channel == __value.channel

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
    '''Hold setpoint action.

    When the pin 35 is pulled high, the output of the corresponding channel immediately changes to the number set in hsp.
    The return value must be a pair of lists: 
    - list1: time of the transition edges of the TTL signal.
    - list2: the output DAC number corresponding to this TTL signal. 

    For instance, a return value of [1000, 2000], [500] means the DAC output is 500 between 1000 and 2000   

    Warning
    ---
    It is the duty of the user to make sure that the passed HSP waveform is compatible across stages. The total number of edges should be twice the number of set points.  
    '''

    def __init__(self, *, channel: int, **kwargs) -> None:
        self.channel = channel
        super().__init__(**kwargs)

    @cache_actions
    async def run_preprocess(self, target: AIO):
        if hsp not in target.ts_mapping:
            raise KeyError(f"hsp is not in ts_mapping of AIO target {target}")
        # handle empty sequence
        if not self.retv[1]:
            return 
        await target.backend.hsp(
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

    def weak_equal(self, __value: object) -> bool:
        return super().weak_equal(__value) and self.channel == __value.channel


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
