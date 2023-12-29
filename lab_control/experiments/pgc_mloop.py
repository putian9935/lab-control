import traceback
from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, inject_lab_into_function, inject_dict_into_function, at_acq_end, at_acq_start
from functools import partial
if __name__ == '__main__':
    from ..lab.in_lab import *
# --- do not change anything above this line ---

import numpy as np
from lab_control.core.config import config
prepare_time = 100*ms


def turn_off_repumpers():
    @TSChannel(channel=19, init_state=1)
    def aom_rf_switch_410_451():
        ''' turn off repumpers '''
        return [0]

    @TSChannel(channel=20, init_state=1)
    def aom_410_master():
        return [0,]

    @TSChannel(channel=37, init_state=1)
    def aom_451_master():
        return [0,]

    @TSChannel(channel=36, init_state=1)
    def aom_410_slave():
        return [0,]


def rp_intensity(intensity):
    @aio_rp(channel=0, action=ramp)
    def intensity_410_master():
        return [0], [2], [intensity]

    @aio_rp(channel=1, action=ramp)
    def intensity_410_slave():
        return [0], [2], [intensity]

    @aio_rp(channel=2, action=ramp)
    def intensity_451_master():
        return [0], [2], [intensity]

    @aio_rp(channel=3, action=ramp)
    def intensity_451_slave():
        return [0], [2], [intensity]


@Experiment(True, 'ts_in', 'remote_config')
def pgc_single(
    load_mot_time=1*s,
    cool_mot_time=3.5*ms,
    tof_time=2.5*ms,
    # vco detuning
    det_mot=40,
    det_low=150,
    det_ramp=1.5*ms,
    det_img=-11,
    # 326 intensity
    intensity_high=.85,
    intensity_low=.45,
    rp_intensity_low=0.1,
    intensity_ramp=1500*us,
    # b-field
    b_field_mot=34,
    b_field_low=34,
    bef_mw_time=4*ms,
    bias_b_field=0.615,
    bias_b_field2=0.594,
    bias_b_field1=0.488,
    exposure_time=200*us,
    exposure_intensity=.97,
    shutdown='fast',
    comment='',
):
    @TSChannel(channel=3, init_state=1)
    def unused3():
        return []

    from .common_stages import prepare, load_mot, cool_mot, cleanup1, background, cleanup2
    everything = dict(globals(), **locals())
    prepare = Stage(duration=prepare_time+.1*s)(prepare, everything)

    load_mot = Stage(duration=load_mot_time)(load_mot, everything)
    # cool_mot = Stage(duration=cool_mot_time+100*us)(cool_mot, everything)

    @Stage()
    def ramp_z_field():
        print(bias_b_field)

        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [-1*ms], [1*ms], [bias_b_field[0]]

        times = np.array([3, 3.5, 4, 5, 6, 7]) * ms
        for start, end, b in zip(times, times[1:], bias_b_field[1:]):
            @aio_zcompServo(channel=0, action=ramp)
            def z_comp_coil_ramp():
                return [start], [end-start], [b]

        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [5*ms], [1*ms], [.66]

    @Stage(duration=bef_mw_time)
    def shutdown():
        turn_off_repumpers()
        rp_intensity(0.01)

        @TSChannel(channel=8)
        def zm_shutter():
            ''' turn off the shutter '''
            return [0]

        @TSChannel(channel=6)
        def zm_rp_shutter():
            return [-1*ms]

        @vco_controller()
        def vco_651_trig():
            return [0], [2*ms], [det_low[0]]

        @aio_zcompServo(channel=1, action=ramp)
        def comp2_coil_ramp():
            return [1*ms], [1*ms], [bias_b_field2]

        @comp_coil1
        def _():
            return [1*ms], [1*ms], [bias_b_field1]

        @coil_servo
        def coil_vref():
            return [-5*ms], [2000], [48]

        @TSChannel(channel=1)
        def igbt0():
            ''' shutdown the magnetic field '''
            return [0]

        @TSChannel(channel=3, init_state=1)
        def unused3():
            return [0]

        @TSChannel(channel=5)
        def field_unlock():
            ''' disengage the coil servo '''
            return [0]

        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            ''' shutdown the MOT beam,'''
            return [-100*us]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [0], [1], [0.01]

    @Stage(duration=cool_mot_time)
    def pgc():
        @TSChannel(channel=56, action=pulse)
        def test_trig():
            return [0]

        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            ''' on the MOT beam,'''
            return [0, cool_mot_time]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [-500, 0], [1, 2], [-0.01, intensity_low]

        @aio_rp(channel=0, action=ramp)
        def intensity_410_master():
            return [-500, 0], [1, 2], [-0.01, rp_intensity_low]

        @aio_rp(channel=1, action=ramp)
        def intensity_410_slave():
            return [-500, 0], [1, 2], [-0.01, rp_intensity_low]

        @aio_rp(channel=2, action=ramp)
        def intensity_451_master():
            return [-500, 0], [1, 2], [-0.01, rp_intensity_low]

        @aio_rp(channel=3, action=ramp)
        def intensity_451_slave():
            return [-500, 0], [1, 2], [-0.01, rp_intensity_low]

        @vco_controller()
        def vco_651_trig():
            return [5*ms], [2*ms], [det_low[1]]

        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [cool_mot_time], [1*ms], [det_img]

        @TSChannel(channel=19, init_state=1)
        def aom_rf_switch_410_451():
            ''' turn on repumpers '''
            return [0, cool_mot_time]

        @TSChannel(channel=20, init_state=1)
        def aom_410_master():
            return [0, cool_mot_time]

        @TSChannel(channel=37, init_state=1)
        def aom_451_master():
            return [0, cool_mot_time]

        @TSChannel(channel=36, init_state=1)
        def aom_410_slave():
            return [0, cool_mot_time]

    @Stage(duration=exposure_time, start_at=pgc.end+tof_time)
    def exposure():
        @TSChannel(channel=10, action=pulse)
        def emccd_trig():
            return [-2*ms]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [-2*ms], [20], [intensity_high]

        @TSChannel(channel=7)
        def mot_aom():
            ''' shine the MOT beam '''
            return [0, exposure_time]

    cleanup1 = Stage(start_at=exposure.end + 100*ms, duration=50 *
                     ms)(inject_dict_into_function(cleanup1, everything))

    cleanup2 = Stage(start_at=cleanup1.end+50 *
                     ms)(partial(cleanup2, det_ramp, det_mot, ))


@inject_lab_into_coroutine
async def pgc_mloop(tof_time, bef_mw_time, *args):
    config_dict = {
        'cool_mot_time': 4.2*ms,
        # 'cool_mot_time': 3.5*ms,
        'tof_time': 6.6*ms,
        # vco detuning
        # 'det_mot': 40,
        # 'det_low': 190,
        'det_mot': -40,
        # 'det_mot': -50,
        'det_low': -170,
        'det_img': -11,
        'det_ramp': 5*ms,
        # 326 intensity
        'intensity_high': 0.97,
        'intensity_low': 0.2,
        'rp_intensity_low': 0.1,
        # 'intensity_high': .7,
        # 'intensity_low': .7,
        'intensity_ramp': 1500*us,
        # b-field
        'b_field_mot': 43,
        'b_field_low': 48,
        # 'b_field_mot': 34,
        # 'b_field_low': 34,
        'exposure_time': 200*us,
        'exposure_intensity': .97,
    }

    remote_config.update_cnt()
    config_dict['bef_mw_time'] = bef_mw_time * 4000 + 3000
    config_dict['bias_b_field1'] = .482
    config_dict['bias_b_field2'] = .504
    config_dict['cool_mot_time'] = 5*ms - config_dict['bef_mw_time'] + 4000
    config_dict['tof_time'] = tof_time
    config_dict['bias_b_field'] = args
    config_dict['intensity_low'] = .97
    config_dict['rp_intensity_low'] = 0.2
    config_dict['det_low'] = [-200, -210]
    await pgc_single(**config_dict)


@inject_lab_into_coroutine
async def main():
    await at_acq_start()
    fname = remote_config.gen_fname_from_dict({})
    end_acq()
    start_acq(fname)
    for tof_time in np.arange(5, 20)*ms:
        await pgc_mloop(
        tof_time, 0.24918076, 0.66788901, 0.53981744, 0.71609362, 0.62803165, 0.65637824, 0.65769436, 0.6376162
        )
    end_acq()
