import importlib.util 
from core import Target, ActionMeta
import asyncio 
from util.run_experiment import * 
import traceback 

async def main(lab_name):
    spec = importlib.util.find_spec('lab.'+lab_name)
    if spec is None: 
        raise ValueError(f"Cannot find lab {lab_name}. Did you put it in lab folder?")
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
        except Exception as e:
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main('sr_lab'))
    # asyncio.run(main('offline_lab'))