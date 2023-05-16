import asyncio
from .util.ts import merge_seq


def set_pulse(cls):
    cls.pulse = True
    return cls


class ActionMeta(type):
    def __init__(cls, *args):
        cls.instances: list[Action] = []
        cls.pulse = False

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
    def __init__(self, signame=None, polarity=False, retv=None) -> None:
        self.signame = signame
        self.retv = retv
        self.polarity = polarity
        type(self).instances.append(self)

    async def run_preprocess(self, target):
        print(
            f'[Warning] Action {type(target).__name__}.{type(self).__name__} has no preprocess to run.')

    def to_time_sequencer(self, target):
        print(
            f'[Warning] Action {type(target).__name__}.{type(self).__name__} has nothing to transform to time sequencer.')
    
    async def run_postprocess(self, target):
        print(
            f'[Warning] Action {type(target).__name__}.{type(self).__name__} has no postprocess to run.')
