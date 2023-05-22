from typing import Any, Coroutine, Optional, Callable
from collections import defaultdict

import asyncio
from .action import Action, ActionMeta
from .util.ts import merge_seq, to_pulse, merge_plot_maps
from types import *


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
                self.actions[act].append(new_action)
        return ret

    async def wait_until_ready(self):
        pass

    def test_precondition(self):
        return True

    async def run_preprocess(self):
        await asyncio.gather(*[act.run_preprocess_cls(self) for act in type(self).supported_actions if act is not None])

    def to_time_sequencer(self):
        return merge_seq(*[to_pulse(act_t.to_time_sequencer_cls(self), act_t.pulse) for act_t in type(self).supported_actions if act_t is not None])

    def to_plot(self, expand_pulse=False, raw=False):
        return merge_plot_maps(*[act_t.to_plot_cls(self, expand_pulse, raw) for act_t in type(self).supported_actions if act_t is not None])

    def test_postcondition(self):
        return True

    async def run_postprocess(self):
        await asyncio.gather(*[act.run_postprocess_cls(self) for act in type(self).supported_actions if act is not None])

    def cleanup(self) -> None:
        self.actions: defaultdict[Action, list[Action]] = defaultdict(list)

    async def close(self):
        pass

    def __str__(self) -> str:
        if not self.__name__:
            return super().__repr__()
        return self.__name__
