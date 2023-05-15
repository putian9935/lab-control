import importlib.util
from core import Target, ActionMeta, TargetMeta
import asyncio
from core.run_experiment import *
import traceback


async def main(lab_name):
    spec = importlib.util.find_spec('lab.'+lab_name)
    if spec is None:
        raise ValueError(
            f"Cannot find lab {lab_name}. Did you put it in lab folder?")
    lab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lab)
    print(f'[INFO] Entered {lab_name}!')

    # parse used targets 
    attr = dict()
    for x in dir(lab):
        obj = lab.__getattribute__(x)
        if isinstance(obj, (Target, ActionMeta)):
            attr[x] = obj
        if isinstance(obj, Target):
            obj.__name__ = x
    list_targets()

    # start background tasks 
    for cls in TargetMeta.instances:
        cls.tasks = []
        for coro in cls.backgrounds:
            cls.tasks.append(asyncio.create_task(coro))
    # wait for targets (e.g., camera) to get ready 
    await wait_until_ready()
    print('[INFO] Target initialized with success')

    while True:
        try:
            exp_name = (await asyncio.get_event_loop().run_in_executor(None, input, 'Input experiment file name:')).strip()
            if not len(exp_name):
                continue
            if exp_name.startswith('!'):
                if exp_name == '!exit':
                    break
                else:
                    print('Unrecognized command!')
                    continue
            await run_exp(exp_name.strip(), attr, )
        except Exception:
            traceback.print_exc()

    for cls in TargetMeta.instances:
        for tsk in cls.tasks:
            if not tsk.done() and not tsk.cancelled():
                tsk.cancel()

    for cls in TargetMeta.instances:
        for target in cls.instances:
            await target.close()

if __name__ == '__main__':
    asyncio.run(main('sr_lab'))
    # asyncio.run(main('offline_lab'))
