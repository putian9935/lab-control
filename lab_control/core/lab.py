import importlib.util
from .target import Target
from .action import ActionMeta
from .run_experiment import *
from typing import Callable 

class Lab:
    """ Lab loader """
    lab_in_use = None 
    def __init__(self, lab_name: str) -> None:
        spec = importlib.util.find_spec('lab_control.lab.'+lab_name)
        if spec is None:
            raise ValueError(
                f"Cannot find lab {lab_name}. Did you put it in lab folder?")
        lab = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lab)
        print(f'[INFO] Entered {lab_name}!')
        self.name = lab_name 
        
        # parse used targets
        self.attr = dict()
        for x in dir(lab):
            obj = lab.__getattribute__(x)
            if isinstance(obj, (Target, ActionMeta, Callable)):
                self.attr[x] = obj
            if isinstance(obj, Target):
                obj.__name__ = x
        Lab.lab_in_use = self 

    async def __aenter__(self):
        # start background tasks
        for cls in all_target_types():
            cls.tasks = []
            for coro in cls.backgrounds:
                cls.tasks.append(asyncio.create_task(coro))
        # wait for targets (e.g., camera) to get ready
        await wait_until_ready()
        print('[INFO] Target(s) initialized with success')
        return self

    async def __aexit__(self, *args):
        for cls in all_target_types():
            for tsk in cls.tasks:
                if not tsk.done() and not tsk.cancelled():
                    tsk.cancel()

        await asyncio.gather(*[target.close() for target in all_target_instances()])
        print(f'[INFO] Target(s) in lab {self.name} closed normally. Bye!')
        Lab.lab_in_use = None 
