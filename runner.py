import importlib.util 
from target import Target 
import asyncio 
from action import Action, ActionMeta 
from run_experiment import * 
from experiment import Experiment 
from parse_input import parse_input 
import traceback 

async def main(lab_name):
    spec = importlib.util.find_spec(lab_name)
    lab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lab)
    
    tasks = []
    for bg in Target.backgrounds:
        tasks.append(asyncio.create_task(bg)) 
    await asyncio.sleep(5)

    attr = dict()
    for x in dir(lab):
        if isinstance(lab.__getattribute__(x), (Target, ActionMeta)):
            attr[x] = lab.__getattribute__(x)

    print('[INFO] Target initialized with success')
    while True: 
        try:
            exp_name = await asyncio.get_event_loop().run_in_executor(None, input, 'Input experiment file name:')
            await run_exp(exp_name.strip(), attr, )
        except Exception as e:
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main('sr_lab'))
    # asyncio.run(main('offline_lab'))