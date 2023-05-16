from .run_experiment import cleanup, run_preprocess, prepare_sequencer_files, run_sequence, test_postcondition, test_precondition, run_postprocess
import time
from typing import Callable

class Experiment:
    def __init__(self, to_fpga=False, ts_fpga=None) -> None:
        if to_fpga:
            if ts_fpga is None:
                raise ValueError("ts_fpga is None but to_fpga is set!")
        self.to_fpga = to_fpga
        self.ts_fpga = ts_fpga

    def __call__(self, f) -> Callable:
        async def ret(*args, **kwds):
            tt = time.perf_counter()
            try:
                ret = f(*args, **kwds)
            except Exception as e:
                cleanup()
                raise type(e)("Cannot parse the Python file. Did you define everything in the lab file?") from e 
            print(f'[INFO] Experiment {f.__name__} parsed in {time.perf_counter()-tt} second(s)!')   
            try:
                tt = time.perf_counter()
                await run_preprocess()
                print(
                    f'[INFO] Prerequisite done in {time.perf_counter()-tt} second(s)!')
                if not test_precondition():
                    raise RuntimeError("Precondition test failed!")
                if self.to_fpga:
                    tt = time.perf_counter()
                    exp_time = prepare_sequencer_files()
                    print(
                        f'[INFO] Sequence prepared in {time.perf_counter()-tt} '
                        'second(s)!')
                    print(
                        f'[INFO] Experiment cycle time: {exp_time/1e6} second(s)')
                    await run_sequence(self.ts_fpga, exp_time)
                    print(f'[INFO] Experiment {f.__name__} sequence done!')    
                await run_postprocess()        
                if not test_postcondition():
                    raise RuntimeError("Postcondition test failed!")
            except:
                raise
            finally:
                cleanup()
                return ret

        return ret
