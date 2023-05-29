from .run_experiment import cleanup, run_preprocess, prepare_sequencer_files, run_sequence, test_postcondition, test_precondition, run_postprocess
from .util.viewer import show_sequences
from .stage import Stage
import time
from .target import PostconditionFail, PreconditionFail
from .types import *
import inspect
from datetime import datetime
from .config import config
from .lab import Lab


class Experiment:
    def __init__(self, to_fpga=False, ts_fpga: str = None) -> None:
        if to_fpga:
            if ts_fpga not in Lab.lab_in_use.attr:
                raise ValueError(f"Cannot find instance {ts_fgpa}!")
        self.to_fpga = to_fpga
        self.ts_fpga = Lab.lab_in_use.attr[ts_fpga]

    def __call__(self, f) -> Awaitable:
        signature = inspect.signature(f)
        async def ret(*args, **kwds):
            def setup_config():
                ba = signature.bind(*args, **kwds)
                ba.apply_defaults()
                config._arguments = ba.arguments
                config._time_stamp = datetime.now()
                config.update_cnt()
                config.exp_name = f.__name__
                config.append_param(config.param_str)
                config.append_fname(config.fname)

            Stage.clear()
            tt = time.perf_counter()
            try:
                # inject lab names to function
                for k, v in Lab.lab_in_use.attr.items():
                    f.__globals__[k] = v
                ret = f(*args, **kwds)
            except Exception as e:
                cleanup()
                raise type(e)(
                    "Cannot parse the Python file. Did you define everything in the lab file?") from e

            print(
                f'[INFO] Experiment {f.__name__} parsed in {time.perf_counter()-tt} second(s)!')
            try:
                setup_config()
                tt = time.perf_counter()
                await run_preprocess()
                print(
                    f'[INFO] Prerequisite done in {time.perf_counter()-tt} second(s)!')
                if not test_precondition():
                    raise PreconditionFail()
                tt = time.perf_counter()
                exp_time = prepare_sequencer_files()
                print(
                    f'[INFO] Sequence prepared in {time.perf_counter()-tt} '
                    'second(s)!')
                print(
                    f'[INFO] Experiment cycle time: {exp_time/1e6} second(s)')
                show_sequences()
                if self.to_fpga and not config.offline:
                    await run_sequence(self.ts_fpga, exp_time)
                    print(f'[INFO] Experiment {f.__name__} sequence done!')
                await run_postprocess()
                if not test_postcondition():
                    raise PostconditionFail()
            except:
                cleanup()
                raise
            else:
                cleanup()
                return ret

        return ret
