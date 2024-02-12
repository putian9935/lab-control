from threading import Thread, get_ident
from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, at_acq_start, inject_lab_into_coroutine, inject_lab_into_function
from lab_control.core.stage import Stage
from lab_control.core.util.img import get_tif_fp, get_tif_latest_single_image, get_roi_count
from lab_control.core.util.find_waist import parse_single_img
import time
from lab_control.core.lab import Lab
if __name__ == '__main__':
    from ..lab.in_lab import *
import asyncio

import mloop.interfaces as mli
import mloop.controllers as mlc


import numpy as np
from lab_control.core.config import config

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
        tsk = loop.create_task(self.coro(15*ms, *params))
        while not tsk.done():
            time.sleep(1e-1)
        im = get_tif_latest_single_image(self.tif_fp)
        fitting_parameter = parse_single_img(im)
        a, b = fitting_parameter[-4:-2]
        a, b = min(a, b), max(a, b)


        tsk = loop.create_task(self.coro(3*ms, *params))
        while not tsk.done():
            time.sleep(1e-1)
        im = get_tif_latest_single_image(self.tif_fp)
        fitting_parameter = parse_single_img(im)
        c, d = fitting_parameter[-4:-2]
        c, d = min(c, d), max(c, d)

        atom_number = (
            get_roi_count(im, (slice(280, 470), slice(500, 750)))
            - get_roi_count(im, (slice(280, 470), slice(200, 450)))
        )
        fitting_parameter = parse_single_img(im)
        bad = np.isnan(a) or np.isnan(b) or atom_number < 1.5e7
        cost = (a * a * b*c*c*d)**.5 / atom_number
        print(f'Fitted parameter is {a} and {b}!')
        print(f'atom number is {atom_number}!')
        cost_dict = {'cost': cost, 'uncer': 20, 'bad': bad}
        return cost_dict


@inject_lab_into_function
def mloop_main():
    remote_config.update_cnt()
    fname = remote_config.gen_fname_from_dict({})
    end_acq()
    start_acq(fname)
    tsk = loop.create_task(at_acq_start())
    while not tsk.done():
        time.sleep(1e-1)

    # First create your interface
    interface = TemperatureMinimizer(
        to_in_helm.conn.modules.lab_control.core.util.img. get_tif_fp(
            fname, remote_config.output_dir),
        pgc_mloop
    )

    # Next create the controller. Provide it with your interface and any options you want to set
    controller = mlc.create_controller(
        interface,
        max_num_runs=100,
        target_cost=-np.inf,
        num_params=8,
        default_bad_cost=50000,
        default_bad_uncertainty=5,
        trust_region=.25,
        min_boundary=[0, .5, .5, .5, .6, .6, .62, .62],
        max_boundary=[1, .8, .8, .8, .8, .8, .68, .68],
        first_params=[.25, .6, .6, .6, .66, .66, .66, .66],
        num_training_runs=50,
    )
    controller.optimize()
    end_acq()

    print('Best parameters found:')
    print(controller.best_params)


async def main():
    task = loop.run_in_executor(None, mloop_main)
    while not task.done() and not task.cancelled():
        await asyncio.sleep(1)
