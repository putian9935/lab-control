from typing import Any, Coroutine
from collections import defaultdict

import asyncio
from core.action import Action, ActionMeta
from util.ts import merge_seq, to_pulse


class TargetMeta(type):
    def __init__(cls, *args):
        cls.supported_actions: set[ActionMeta] = set((None,))
        cls.instances: list[Target] = []
        cls.default_action: ActionMeta = None
        cls.backgrounds: list[Coroutine] = []

    def take_note(cls, action_cls):
        cls.supported_actions.add(action_cls)
        return action_cls

    def set_default(cls, action_cls):
        cls.default_action = action_cls
        return action_cls


class Target(metaclass=TargetMeta):
    def __init__(self) -> None:
        self.actions: defaultdict[Action, list[Action]] = defaultdict(list)
        type(self).instances.append(self)

    def __call__(self,  action=None, **kwds: Any) -> Any:
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
        return merge_seq(*[to_pulse(act.to_time_sequencer_cls(self), act.pulse) for act in type(self).supported_actions if act is not None])

    def run_postprocess(self) -> None:
        self.actions: defaultdict[Action, list[Action]] = defaultdict(list)

    def test_postcondition(self):
        return True 
    
    def close(self):
        pass
