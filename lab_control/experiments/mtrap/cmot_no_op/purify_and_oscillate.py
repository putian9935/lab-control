from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, inject_lab_into_function, inject_dict_into_function, acquisition
from functools import partial
if __name__ == '__main__':
    from ..lab.in_lab import *
# --- do not change anything above this line ---

import numpy as np
prepare_time = 100*ms


@Experiment(True, 'ts_in', 'remote_config')
def single_shot(
    load_mot_time=3*s, 
    # load_mot_time=1*s, 
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
    intensity_ramp=1500*us,
    # b-field
    b_field_mot=34,
    b_field_low=34,
    # SG experiment
    sg_field=35, 
    # odt 
    shutoff_410=1*ms,
    odt_load_time=10*ms, 
    odt_load_mot_time=3*ms,
    odt_hold_time=40*ms, 
    odt_ramp_time=3*ms,
    odt_start_time=0,
    spin_pol_time=150, 
    bias_ramp_time=20*ms, 
    trap_oscillation_period=1*ms,
    mtrap_hold_time=100*ms, 
    odt_high=.96,
    exposure_time=200*us,
    bias_b_field=.604,
    trap_b_field=50, 
    trap_ramp_up=20*ms,
    purify_b_field=15, 
    trap_low_field=20,
    shutdown='fast',
    take_background = False
):
    @TSChannel(channel=3, init_state=1)
    def igbt_34():
        return []

    from ...common_stages import prepare, load_mot, cool_mot, cleanup1, background, cleanup2 
    everything = dict(globals(), **locals())
    prepare = Stage(duration=prepare_time+.1*s)(prepare, everything)

    load_mot = Stage(duration=load_mot_time)(load_mot,everything)
    cool_mot = Stage(duration=cool_mot_time+100*us)(cool_mot, everything)

    

    @Stage(duration=mtrap_hold_time)
    def hold_mtrap():
        @aio_zcompServo(channel=1, action=ramp)
        def comp2_coil_ramp():
            return [30, ], [200], [.510]
        

        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            ''' shutdown the MOT beam,'''
            return [-100*us]

        @TSChannel(pulse, channel=4)
        def _():
            return [0]
        @coil_servo
        def coil_vref():
            return [30*ms, ], [250*ms], [purify_b_field]
            # return [30*ms, ], [250*ms], [purify_b_field]
            # return [50*ms, ], [45*ms], [purify_b_field]
        
        
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [300*ms, ], [500], [.63-0.005]
            
        @coil_servo
        def coil_vref():
            return [350*ms, ], [150*ms], [trap_b_field]
            # return [350*ms, ], [80*ms], [trap_b_field]
        
        
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [510*ms, ], [1000], [.63-0.22]
            # return [510*ms, ], [500], [.63-0.2]
            # return [280*ms, ], [500], [.63-0.22]
        
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

        @TSChannel(channel=25)
        def mot_top_shutter():
            ''' turn off the shutter '''
            return [0*ms]

        @TSChannel(channel=27)
        def mot_xy_shutter():
            ''' turn off the shutter '''
            return [0*ms]
        @TSChannel(channel=56, action=pulse) 
        def test_trig():
            return [0]

        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [0*ms], [5*ms], [-800]
        
        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            ''' shutdown the MOT beam,'''
            return [3*ms, 3.1*ms]

        
        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [0], [6*ms], [0.01]
        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [tof_time - 2*ms], [20], [-.01]
            
    @Stage()
    def turn_off():
        @TSChannel(channel=1)
        def igbt0():
            ''' shutdown the magnetic field '''
            return [0]

        @TSChannel(channel=5)
        def field_unlock():
            ''' disengage the coil servo '''
            return [0]
        
        @TSChannel(channel=3,)
        def igbt_34():
            return [0]

    @Stage(duration=tof_time, )
    def repump():
        # return
        @TSChannel(channel=19)
        def aom_rf_switch_410_451():
            ''' shine repumpers '''
            return [0, exposure_time]
        
        @TSChannel(channel=20)
        def aom_410_master():
            return [0, exposure_time]
        
        @TSChannel(channel=36)
        def aom_410_slave():
            return [0,exposure_time]
        
        @TSChannel(channel=37)
        def aom_451_master():
            ''' turn on repumpers '''
            return [0,exposure_time]
    @Stage(duration=exposure_time)
    def exposure():
        @TSChannel(channel=10, action=pulse)
        def emccd_trig():
            return [ - 2*ms]
        @TSChannel(channel=25)
        def mot_top_shutter():
            ''' turn off the shutter '''
            return [-3*ms]

        @TSChannel(channel=27)
        def mot_xy_shutter():
            ''' turn off the shutter '''
            return [-3*ms]
            
        @TSChannel(channel=7)
        def mot_aom():
            ''' shine the MOT beam '''
            return [0, exposure_time]

        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [-16*ms], [5*ms], [det_img]
        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [-250], [20], [.97]

        @TSChannel(channel=24)
        def cmos_camera():
            return [-250, 500]
        
        @TSChannel(channel=19)
        def aom_rf_switch_410_451():
            ''' shine repumpers '''
            return [0, exposure_time]
        
        @TSChannel(channel=20)
        def aom_410_master():
            return [0, exposure_time]
        
        @TSChannel(channel=36)
        def aom_410_slave():
            return [0,exposure_time]
        
        @TSChannel(channel=37)
        def aom_451_master():
            ''' turn on repumpers '''
            return [0,exposure_time]

    cleanup1 = Stage(start_at=repump.end + 100*ms, duration=50*ms)(inject_dict_into_function(cleanup1, everything))


    # background = Stage()(inject_dict_into_function(background, everything))

    cleanup2 = Stage(start_at=cleanup1.end+50*ms)(partial(cleanup2,det_ramp, det_mot, ))
  
@inject_lab_into_coroutine
async def main():
    config_dict = {
        'cool_mot_time': 4.2*ms,
        # 'cool_mot_time': 3.5*ms,
        'tof_time': 4*ms,
        # vco detuning
        'det_mot': -40,
        'det_low': -140,
        'det_img': -6, 
        'det_ramp': 3*ms,
        # 326 intensity
        'intensity_high': 0.97,
        'intensity_low': 0.97,
        # 'intensity_high': .7,
        # 'intensity_low': .7,
        'intensity_ramp': 1500*us,
        # b-field
        'b_field_mot': 43,
        # 'b_field_low': 48,
        'b_field_low': 43,
        'exposure_time': 300*us, 
        'take_background':False
    }
    remote_config.update_cnt()
    from tqdm import tqdm 
    end_acq()
    while True:
        for trap_b_field in [40, ]:
            for purify_b_field in [34, 23, 17, 14]:
            # for purify_b_field in [14, 17, 23, 34]:
                async with acquisition():
                    # for bias_b_field in tqdm(np.arange(.4, .8, 0.005)):
                    # 14, 17, 23, 34
                    start_acq(remote_config.gen_fname_from_dict(config_dict))
                    for mtrap_hold_time in tqdm(np.arange(500, 750, 2)*ms):
                    # for mtrap_hold_time in tqdm(np.arange(70, 300, 2)*ms):
                    # for trap_low_field in tqdm(np.arange(22, 46, 2)):
                    # for trap_low_field in [13.5]:
                        # config_dict['mtrap_hold_time'] = 70*ms
                        # config_dict['mtrap_hold_time'] = 400*ms
                        config_dict['mtrap_hold_time'] = mtrap_hold_time
                        # config_dict['tof_time'] = 2.5*ms
                        # config_dict['tof_time'] = 6.6*ms
                        # config_dict['tof_time'] = 10*ms
                        config_dict['tof_time'] = 8*ms
                        # config_dict['bias_b_field'] = .5
                        # config_dict['trap_low_field'] = trap_low_field
                        config_dict['bias_b_field'] = .54
                        # config_dict['bias_ramp_time'] = 200
                        config_dict['trap_b_field'] = trap_b_field
                        config_dict['purify_b_field'] = purify_b_field
                        config_dict['det_img'] = -6
                        await single_shot(**config_dict)
                    end_acq()
        