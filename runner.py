from lab_control.core import PreconditionFail, PostconditionFail
import asyncio
from lab_control.core.run_experiment import *
import traceback
from lab_control.core.config import config
from lab_control.core.lab import Lab


async def main(lab_name):
    async with Lab(lab_name) as lab:
        print('''[INFO] Special commands: !exit, !ls targets, !ls actions, !help <action>, !config <k=v>''')
        while True:
            try:
                exp_name = (
                    await asyncio.get_event_loop().
                    run_in_executor(None, input, 'Input experiment file name:')).strip()
                if not len(exp_name):
                    continue
                if exp_name.startswith('!'):
                    if exp_name == '!exit':
                        break
                    elif exp_name == '!ls targets':
                        list_targets()
                    elif exp_name == '!ls actions':
                        list_actions()
                    elif exp_name.startswith('!help'):
                        name = exp_name[5:].strip()
                        act = to_action(name)
                        if act is None:
                            print(
                                f'Unknown action type {name}. Did you include the correpsonding target type in the lab file? ')
                        else:
                            get_action_usage(act)
                    elif exp_name.startswith('!config'):
                        cmd = exp_name[7:].strip()
                        config.update(cmd)
                    elif exp_name == '!reload':
                        logging.info(f'Reloading lab {lab_name}')
                        await lab.__aexit__()
                        lab = Lab(lab_name) 
                        await lab.__aenter__()
                    else:
                        print('Unrecognized command!')
                else:
                    await run_exp(exp_name.strip())
            except (PreconditionFail, PostconditionFail):
                print(
                    '[ERROR] Pre- or Post-condiction failed! Please go over through the messages starting with [ERROR] and fix them.')
            except Exception:
                traceback.print_exc()

if __name__ == '__main__':
    # asyncio.run(main('in_lab'))
    asyncio.run(main('offline_lab'))
    # asyncio.run(main('remote_test'))
    # asyncio.run(main('remote'))
