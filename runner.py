import importlib.util
from lab_control.core import Target, ActionMeta
import asyncio
from lab_control.core.run_experiment import *
import traceback


async def main(lab_name):
    spec = importlib.util.find_spec('lab_control.lab.'+lab_name)
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

    # start background tasks 
    for cls in all_target_types():
        cls.tasks = []
        for coro in cls.backgrounds:
            cls.tasks.append(asyncio.create_task(coro))
    # wait for targets (e.g., camera) to get ready 
    await wait_until_ready()
    print('[INFO] Target(s) initialized with success')
    print('[INFO] Special commands: !exit, !ls targets, !ls actions')
    while True:
        try:
            exp_name = (await asyncio.get_event_loop().run_in_executor(None, input, 'Input experiment file name:')).strip()
            if not len(exp_name):
                continue
            if exp_name.startswith('!'):
                if exp_name == '!exit':
                    break
                elif exp_name == '!ls targets':
                    list_targets()
                elif exp_name == '!ls actions':
                    list_actions()
                else:
                    print('Unrecognized command!')
            else:
                await run_exp(exp_name.strip(), attr, )
        except Exception:
            traceback.print_exc()

    for cls in all_target_types():
        for tsk in cls.tasks:
            if not tsk.done() and not tsk.cancelled():
                tsk.cancel()

    await asyncio.gather(*[target.close() for target in all_target_instances()])
    print('[INFO] Target(s) closed normally. Bye!')

if __name__ == '__main__':
    # asyncio.run(main('sr_lab'))
    # asyncio.run(main('offline_lab_remote'))
    asyncio.run(main('remote_test'))
    # asyncio.run(main('remote'))
