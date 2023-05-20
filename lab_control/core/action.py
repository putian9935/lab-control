import asyncio
from .util.ts import merge_seq
from collections import defaultdict
from .stage import Stage
from typing import List, Callable, Optional, Dict, Tuple


def set_pulse(cls):
    cls.pulse = True
    return cls


class ActionMeta(type):
    instances = {}
    targets = defaultdict(str)

    def __init__(cls, *args):
        cls.instances: list[Action] = []
        cls.pulse = False
        ActionMeta.instances[cls.__name__] = cls
        def add_offset(f: Callable):
            def ret_func(self, *args, **kwds):
                _ret = f(self, *args, **kwds) 
                ret = {}
                if isinstance(_ret, dict):
                    for k, v in _ret.items():
                        ret[k] = self.add_offset(v[0]), v[1], v[2]
                return ret 
            return ret_func
        cls.to_time_sequencer = add_offset(cls.to_time_sequencer)

    async def run_preprocess_cls(cls, target):
        await asyncio.gather(*[inst.run_preprocess(target)
                               for inst in cls.instances
                               if inst in target.actions[cls]])

    def to_time_sequencer_cls(cls, target):
        return merge_seq(*[inst.to_time_sequencer(target)
                           for inst in cls.instances
                           if inst in target.actions[cls]])

    async def run_postprocess_cls(cls, target):
        await asyncio.gather(*[inst.run_postprocess(target)
                               for inst in cls.instances
                               if inst in target.actions[cls]])

    def cleanup(cls):
        cls.instances: list[Action] = []

    def __str__(cls) -> str:
        return cls.__name__


class Action(metaclass=ActionMeta):
    def __init__(self, signame=None, polarity=False, retv=None, init_state=None) -> None:
        self.signame = signame
        self.retv = retv
        self.polarity = polarity
        self._offset = Stage.cur  # offset in time marked by Stage
        if init_state is not None:
            self.polarity = init_state
        type(self).instances.append(self)

    def add_offset(self, l: List):
        return [x + self._offset for x in l]

    async def run_preprocess(self, target):
        print(
            f'[Warning] Action {type(target).__name__}.{type(self).__name__} has no preprocess to run.')

    def to_time_sequencer(self, target):
        print(
            f'[Warning] Action {type(target).__name__}.{type(self).__name__} has nothing to transform to time sequencer.')

    async def run_postprocess(self, target):
        print(
            f'[Warning] Action {type(target).__name__}.{type(self).__name__} has no postprocess to run.')
