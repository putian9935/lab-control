from threading import Thread, get_ident
from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, at_acq_start
from lab_control.core.stage import Stage
from lab_control.core.util.img import get_tif_fp, get_tif_latest_single_image
from lab_control.core.util.find_waist import parse_single_img 
import time 

if __name__ == '__main__':
    from ..lab.in_lab import *
import asyncio

import mloop.interfaces as mli
import mloop.controllers as mlc
from .pgc_mloop import pgc_mloop

loop = asyncio.get_event_loop()

class TemperatureMinimizer(mli.Interface):
    """ 
    Minimize temperature 
    
    Parameter
    --- 
    - tif_fp: File handle for TIFF image 
    - coro: coroutine function of the experiment  
    """
    def __init__(self, tif_fp, coro,):
        super(TemperatureMinimizer, self).__init__()

        self.tif_fp = tif_fp
        self.coro = coro 

    def get_next_cost_dict(self, params_dict):
        params = params_dict['params']
        tsk = loop.create_task(self.coro(*params))
        while not tsk.done():
            time.sleep(1e-1)

        fitting_parameter = parse_single_img(get_tif_latest_single_image(self.tif_fp)) 

        a, b = fitting_parameter[-4:-2] 
        bad = np.isnan(a) or np.isnan(b) 
        cost = (a + b) 
        cost_dict = {'cost': cost, 'uncer': 5, 'bad': bad}
        return cost_dict


def mloop_main():
    remote_config.update_cnt()
    fname = remote_config.gen_fname_from_dict({})
    start_acq(fname)
    # loop.create_task(at_acq_start())
    # First create your interface
    interface = TemperatureMinimizer(
        get_tif_fp(fname, remote_config.output_dir),
        pgc_mloop
    )

    # Next create the controller. Provide it with your interface and any options you want to set
    controller = mlc.create_controller(interface,
                                       max_num_runs=2,
                                       target_cost=-np.inf,
                                       num_params=5,
                                       min_boundary=[.4]*5,
                                       max_boundary=[.9]*5)
    controller.optimize()
    end_acq()

    print('Best parameters found:')
    print(controller.best_params)


async def main():
    task = loop.run_in_executor(None, mloop_main)
    while not task.done() and not task.cancelled():
        await asyncio.sleep(1)
