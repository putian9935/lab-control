from __future__ import annotations
import asyncio
from .util.ts import merge_seq, merge_plot_maps
from collections import defaultdict
from .stage import Stage
from typing import List, Callable, Optional, Dict, Tuple
from functools import wraps
from .types import *
import logging 

logger = logging.getLogger('core.action')
logger.setLevel(logging.INFO)

import typing
if typing.TYPE_CHECKING:
    from .target import Target


def set_pulse(cls):
    cls.pulse = True
    return cls


class ActionMeta(type):
    instances = {}
    targets = defaultdict(list)

    def __new__(cls, name, bases, attr, **kwds):
        return type.__new__(cls, name, bases, attr)

    def __init__(cls, new, bases, attr, offset=False):
        cls.instances: list[Action] = []
        cls.last_target_actions: Dict[Target, List[Action]] = {}
        cls.pulse = False
        cls._offset: bool = offset  # the library writer may override the default behavior
        ActionMeta.instances[cls.__name__] = cls

    async def run_preprocess_cls(cls, target: 'Target'):
        await asyncio.gather(*[inst.run_preprocess(target)
                               for inst in target.actions[cls]])

    def to_time_sequencer_cls(cls, target: 'Target'):
        return merge_seq(*[inst.to_time_sequencer(target)
                           for inst in target.actions[cls]])

    def to_plot_cls(cls, target: 'Target', **kwargs):
        return merge_plot_maps(*[inst.to_plot(target, **kwargs)
                                 for inst in target.actions[cls]])

    async def run_postprocess_cls(cls, target: 'Target'):
        await asyncio.gather(*[inst.run_postprocess(target)
                               for inst in target.actions[cls]])

    def cleanup(cls):
        cls.instances: list[Action] = []

    def __str__(cls) -> str:
        return cls.__name__


class Action(metaclass=ActionMeta):
    def __init__(self, signame=None, polarity=False, retv=None, init_state=None, is_temp=False) -> None:
        self.signame = signame

        self.retv = retv
        if self.retv is not None:
            if isinstance(self.retv, tuple):
                self.retv = self.add_offset(
                    self.retv[0]), *self.retv[1:]
            else:
                self.retv = self.add_offset(self.retv)

        self.polarity = polarity
        if init_state is not None:
            self.polarity = init_state
        if not is_temp:
            self._used = False
            for x in type(self).instances:
                if self.weak_equal(x):
                    self._used = True
                    x.extend(self)
                    return
            type(self).instances.append(self)


    def add_offset(self, l: List):
        """ Handle temporal offset due to Stages """
        cls = type(self)
        if cls.__base__ is object:
            return l
        # handle inheritance: if the base class is offset, then the subclass needs not to
        elif not cls._offset and cls.__base__._offset:
            cls._offset = True
            return l
        # ensure everything is rounded 
        return [int(x + Stage.cur) for x in l]

    async def run_preprocess(self, target: 'Target'):
        logger.debug(
            f'Action {type(target).__name__}.{type(self).__name__} has no preprocess to run.')

    def to_time_sequencer(self, target: 'Target') -> Optional[ts_map]:
        logger.debug(
            f'Action {type(target).__name__}.{type(self).__name__} has nothing to transform to time sequencer.')

    def to_plot(self, target: 'Target', *args, **kwargs) -> Optional[plot_map]:
        logger.debug(
            f'Action {type(target).__name__}.{type(self).__name__} has nothing to plot.')

    async def run_postprocess(self, target: 'Target'):
        logger.debug(
            f'Action {type(target).__name__}.{type(self).__name__} has no postprocess to run.')

    def extend(self, new):
        if type(self) != type(new):
            raise TypeError("Non-comparable type!")
        if isinstance(self.retv, tuple):
            for l, ll in zip(self.retv, new.retv):
                l.extend(ll)
        elif isinstance(self.retv, list):
            self.retv.extend(new.retv)

    def __eq__(self, __value: object) -> bool:
        ''' compare full property  '''
        if type(self) == type(__value):
            return self.signame == __value.signame and self.retv == __value.retv
        raise TypeError("Non-comparable type!")
    
    def weak_equal(self, __value: object) -> bool:
        ''' allow return value to be different, since they are not essential '''
        return self.signame == __value.signame
    
    def __repr__(self) -> str:
        return f'{type(self).__name__}:[{self.retv}]'