from typing import Any, Coroutine, Optional, Callable
from collections import defaultdict

import asyncio
from .action import Action, ActionMeta
from .util.ts import merge_seq, to_pulse, merge_plot_maps
from types import *
from .config import config
from functools import wraps


class PreconditionFail(Exception):
    pass


class PostconditionFail(Exception):
    pass


class TargetMeta(type):
    instances = []

    def __init__(cls, *args):
        cls.supported_actions: set[ActionMeta] = set((None,))
        cls.instances: list[Target] = []
        cls.default_action: Optional[ActionMeta] = None
        cls.backgrounds: list[Coroutine] = []
        TargetMeta.instances.append(cls)

    def take_note(cls, action_cls: ActionMeta):
        cls.supported_actions.add(action_cls)
        ActionMeta.targets[action_cls.__name__] = cls.__name__
        return action_cls

    def set_default(cls, action_cls: ActionMeta):
        cls.default_action = action_cls
        return action_cls


class Target(metaclass=TargetMeta):
    def __init__(self) -> None:
        self.actions: defaultdict[ActionMeta, list[Action]] = defaultdict(list)
        self.loaded = False
        self.__name__: Optional[str] = None
        type(self).instances.append(self)

    def __call__(self,  action: ActionMeta = None, **kwds: Any) -> Callable:
        if action not in type(self).supported_actions:
            raise ValueError(f"Unsupported action {action} for {type(self)}")

        def ret(f):
            if action is not None:
                act = action
            elif type(self).default_action is not None:
                act = type(self).default_action
            else:
                raise ValueError(
                    f"Default action for target {type(self)} is not specified!")
            try:
                new_action = act(**kwds, signame=f.__name__, retv=f())
            except TypeError as e:
                raise TypeError(
                    f'Incorrect argument count for action {type(self).__name__}.{act.__name__}') from e
            else:
                if not new_action._used:
                    self.actions[act].append(new_action)
        return ret

    def ensure_loaded(f):
        if not asyncio.iscoroutinefunction(f):
            def ret(self, *args, **kwds):
                if not self.loaded:
                    if config.strict:
                        raise RuntimeError(
                            f'Target {self} of type {type(self).__name__} is not loaded!')
                    else:
                        print(
                            f'[WARNING] Target {self} of type {type(self).__name__} is not loaded!')
                return f(self, *args, **kwds)
        else:
            async def ret(self, *args, **kwds):
                if not self.loaded:
                    if config.strict:
                        raise RuntimeError(
                            f'Target {self} of type {type(self).__name__} is not loaded!')
                    else:
                        print(
                            f'[WARNING] Target {self} of type {type(self).__name__} is not loaded!')
                return await f(self, *args, **kwds)
        return ret

    def disable_if_offline(f):
        def ret(self, *args, **kwds):
            if config.offline:
                if asyncio.iscoroutinefunction(f):
                    async def empty(): pass
                    return empty()
                return
            return f(self, *args, **kwds)
        return ret

    def load_wrapper(loader):
        def ret(self, *args, **kwds):
            try:
                loader(self, *args, **kwds)
            except Exception as e:
                print(
                    f'[ERROR] Cannot load {self} of type {type(self).__name__}:', e)
            else:
                self.loaded = True
        return ret

    async def wait_until_ready(self):
        pass

    def test_precondition(self):
        return True

    @disable_if_offline
    @ensure_loaded
    async def run_preprocess(self):
        await asyncio.gather(*[act.run_preprocess_cls(self) for act in type(self).supported_actions if act is not None])

    def to_time_sequencer(self):
        return merge_seq(*[to_pulse(act_t.to_time_sequencer_cls(self), act_t.pulse) for act_t in type(self).supported_actions if act_t is not None])

    def to_plot(self, expand_pulse=False, raw=False):
        return merge_plot_maps(*[act_t.to_plot_cls(self, expand_pulse=expand_pulse, raw=raw) for act_t in type(self).supported_actions if act_t is not None])

    def test_postcondition(self):
        return True

    @disable_if_offline
    @ensure_loaded
    async def run_postprocess(self):
        await asyncio.gather(*[act.run_postprocess_cls(self) for act in type(self).supported_actions if act is not None])

    def cleanup(self) -> None:
        self.actions: defaultdict[Action, list[Action]] = defaultdict(list)

    @ensure_loaded
    async def close(self):
        pass

    @disable_if_offline
    @load_wrapper
    def load(self, *args, **kwds):
        pass

    def __str__(self) -> str:
        if not self.__name__:
            return super().__repr__()
        return self.__name__
