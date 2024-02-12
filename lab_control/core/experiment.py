from .run_experiment import cleanup, run_preprocess, prepare_sequencer_files, run_sequence, test_postcondition, test_precondition, run_postprocess, at_acq_end, at_acq_start, AbortExperiment
from .util.viewer import show_sequences
from .stage import Stage
import time
from .target import PostconditionFail, PreconditionFail
from .types import *
import inspect
from datetime import datetime
from .config import config
from .lab import Lab
from functools import wraps
import logging 
import msvcrt 
import asyncio 
from .util.inject import inject_dict_into_function 

async def wait_for(char: str):
    ''' wait for user to press `char` '''
    ch = char.encode()
    while True:
        if msvcrt.kbhit():
            if msvcrt.getch() == ch:
                break 
        await asyncio.sleep(0.1)
    logging.debug(f'Press {char} event detected.')

async def wait_for_q():
    ''' quit the acquisition after this one finishes '''
    await wait_for('q')
    

def inject_lab_into_coroutine(f):
    """ inject lab information into a coroutine """
    @wraps(f)
    async def ret(*args, **kwds):
        for k, v in Lab.lab_in_use.attr.items():
            f.__globals__[k] = v
        return await f(*args, **kwds)
    return ret 

def inject_lab_into_function(f):
    """ inject lab information into a function """
    return inject_dict_into_function(f, Lab.lab_in_use.attr)


def deal_with_condition_fail():
    """ deal with pre-/post-condition failure 
    
    Provides two options (from user input):
    - a: abort the experiment 
    - c: continue the experiment 
    """
    x = input("""Pre-/post-condition failure detected! Enter [a/c/f]?
    - a: abort the experiment;  
    - c: continue the experiment; 
    - f: force continue the experiment
            """)
    
    while True:
        if x == 'a':
            return False 
        if x == 'c':
            return 
        if x == 'f':
            return True
        x = input("Enter [a/c/f]?")

class Experiment:
    def __init__(self, to_fpga=False, ts_fpga: str = None, config_: str =None) -> None:
        self.to_fpga = to_fpga
        if to_fpga:
            if ts_fpga is None:
                raise ValueError("Please specify time sequencer FPGA instance!")
            if ts_fpga not in Lab.lab_in_use.attr:
                raise ValueError(f"Cannot find instance {ts_fpga}!")
            self.ts_fpga = Lab.lab_in_use.attr[ts_fpga]
        if config_ is None:
            config_ = 'config' 
        self.config =  Lab.lab_in_use.attr[config_]

    def __call__(self, f) -> Awaitable:
        signature = inspect.signature(f)

        async def ret(*args, **kwds):
            ttt =  time.perf_counter()
            tt = time.perf_counter()
            def setup_config():
                ba = signature.bind(*args, **kwds)
                ba.apply_defaults()
                self.config._arguments = ba.arguments
                self.config._time_stamp = datetime.now()
                self.config.update_cnt()
                self.config.exp_name = f.__name__
                self.config.append_param()
                self.config.append_fname()
            
            Stage.clear()
            try:
                # inject lab names to function
                for k, v in Lab.lab_in_use.attr.items():
                    f.__globals__[k] = v
                ret = f(*args, **kwds)
            except Exception as e:
                cleanup()
                raise type(e)(
                    "Cannot parse the Python file. Did you define everything in the lab file?") from e
            # add taskes to detect keyboard events 
            keypress_tasks = {'q':asyncio.create_task(wait_for_q())}
            logging.debug(
                f'Experiment {f.__name__} parsed in {time.perf_counter()-tt} second(s)!')
            try:
                tt = time.perf_counter()
                config_job = asyncio.to_thread(setup_config)
                logging.debug(
                    f'Setup done in {time.perf_counter()-tt} second(s)!')
                await run_preprocess()
                logging.debug(
                    f'Prerequisite done in {time.perf_counter()-tt} second(s)!')
                tt = time.perf_counter()
                while not test_precondition():
                    action = deal_with_condition_fail() 
                    if action is True:
                        break 
                    if action is False: 
                        raise PreconditionFail()
                logging.debug(
                    f'Precondition done in {time.perf_counter()-tt} second(s)!')
                tt = time.perf_counter()
                exp_time, ti, dt2 = prepare_sequencer_files()
                if config.view:
                    show_sequences()
                logging.debug(
                    f'Sequence prepared in {time.perf_counter()-tt} second(s)!')
                tt = time.perf_counter()
                if self.to_fpga and not config.offline:
                    await asyncio.gather(
                        run_sequence(self.ts_fpga, exp_time, ti, dt2),
                                            config_job
                    )
                    logging.info(f'Experiment {f.__name__} sequence done!')
                logging.debug(
                    f'Sequence done in {time.perf_counter()-tt} second(s)!')
                tt = time.perf_counter()
                await run_postprocess()
                logging.debug(
                    f'Postprocess done in {time.perf_counter()-tt} second(s)!')
                tt = time.perf_counter()
                if not test_postcondition():
                    raise PostconditionFail()
                logging.debug(
                    f'Postcondition done in {time.perf_counter()-tt} second(s)!')
                if keypress_tasks['q'].done():
                    raise AbortExperiment
            except:
                # any exception aborts the experiment and the acquisition 
                for task in keypress_tasks.values():
                    if not task.cancelled() and not task.done():
                        task.cancel()
                cleanup()
                await at_acq_end()
                raise
            else:
                tt = time.perf_counter()
                for task in keypress_tasks.values():
                    if not task.cancelled() and not task.done():
                        task.cancel()
                cleanup()
                logging.debug(
                    f'Cleanup done in {time.perf_counter()-tt} second(s)!')
            logging.debug(f'experiment done all in {time.perf_counter()-ttt}')
        return ret

from contextlib import asynccontextmanager 

@asynccontextmanager
async def acquisition(spool_data=None):
    try:
        await at_acq_start()
        if spool_data is not None:
            raise NotImplementedError("spool_data is not implemented") 
        yield 
    finally:
        await at_acq_end() 
    
        