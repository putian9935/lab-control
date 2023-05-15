from typing import Any

from util.run_experiment import run_postprocess, run_preprocess, prepare_sequencer_files, run_sequence
import time


class Experiment:
    def __init__(self, to_fpga=False, ts_fpga=None) -> None:
        if to_fpga:
            if ts_fpga is None:
                raise ValueError("ts_fpga is None but to_fpga is set!")
        self.to_fpga = to_fpga
        self.ts_fpga = ts_fpga

    def __call__(self, f) -> Any:
        async def ret(*args, **kwds):
            tt = time.perf_counter()
            ret = f(*args, **kwds)
            print(f'[INFO] Experiment {f.__name__} parsed in {time.perf_counter()-tt} second(s)!')
            tt = time.perf_counter()
            await run_preprocess()
            print(
                f'[INFO] Prerequisite done in {time.perf_counter()-tt} second(s)!')
            if self.to_fpga:
                tt = time.perf_counter()
                exp_time = prepare_sequencer_files()
                print(
                    f'[INFO] Sequence prepared in {time.perf_counter()-tt}'
                    'second(s)!')
                print(
                    f'[INFO] Experiment cycle time: {exp_time/1e6} second(s)')
                await run_sequence(self.ts_fpga, exp_time)
                print(f'[INFO] Experiment {f.__name__} sequence done!')
            run_postprocess()
            return ret

        return ret
