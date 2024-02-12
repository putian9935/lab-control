from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, inject_lab_into_function, inject_dict_into_function, at_acq_start
from functools import partial
if __name__ == '__main__':
    from ..lab.in_lab import *
# --- do not change anything above this line ---

import numpy as np
from lab_control.core.config import config
prepare_time = 100*ms


@Experiment(True, 'ts_in')
def single_shot(
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
    rf_final_freq=20,
    trap_ramp_up=20*ms,
    trap_low_field=20,
    shutdown='fast',
    take_background = False
):
    @TSChannel(channel=3, init_state=1)
    def igbt_34():
        return []
    
    @rf_knife_freq
    def _():
        return [0, ], [100,], [10]
    
    from .common_stages import prepare, load_mot, cool_mot, cleanup1, background, cleanup2 
    everything = dict(globals(), **locals())
    prepare = Stage(duration=prepare_time+.1*s)(prepare, everything)

    load_mot = Stage(duration=load_mot_time)(load_mot,everything)
    cool_mot = Stage(duration=cool_mot_time+100*us)(cool_mot, everything)
    

    @Stage(duration=mtrap_hold_time)
    def hold_mtrap():

        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            ''' shutdown the MOT beam,'''
            return [1.2*ms]


        @coil_servo
        def coil_vref():
            return [0, ], [150*ms], [trap_b_field]
        
        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [0], [50], [0.05]
        
        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [0], [.8*ms], [0.01]
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

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [tof_time - 2*ms], [20], [-.01]
            
        @rf_knife_switch
        def _():
            return [150*ms]
    
        @rf_knife_freq
        def _():
            return [150*ms], [450*ms], [rf_final_freq]
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
        pass 
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
            return [-16*ms], [8*ms], [det_img]
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


    background = Stage()(inject_dict_into_function(background, everything))

    cleanup2 = Stage(start_at=background.end+50*ms)(partial(cleanup2,det_ramp, det_mot, ))
  
@inject_lab_into_coroutine
async def main():
    config_dict = {
        'cool_mot_time': 4.2*ms,
        # 'cool_mot_time': 3.5*ms,
        'tof_time': 50*ms,
        # vco detuning
        # 'det_mot': 40,
        # 'det_low': 190,
        'det_mot': -40,
        'det_low': -110,
        'det_img': -11, 
        'det_ramp': 3*ms,
        # 326 intensity
        'intensity_high': 0.97,
        'intensity_low': 0.97,
        # 'intensity_high': .7,
        # 'intensity_low': .7,
        'intensity_ramp': 1500*us,
        # b-field
        'b_field_mot': 43,
        'b_field_low': 43,

        # 'b_field_mot': 34,
        # 'b_field_low': 34,
        'exposure_time': 200*us, 
        'take_background':False
    }

    config.update_cnt()
    await at_acq_start()
    from tqdm import tqdm 
    end_acq()
    while True:  
        for spin_pol_time in [1, 150, ]:
            for bias_ramp_time in [200,]:
                start_acq(config.gen_fname_from_dict(config_dict))
                await at_acq_start()
                for rf_final_freq in tqdm(np.arange(8, 0, -0.2)):
                # for trap_low_field in tqdm(np.arange(22, 46, 2)):
                # for trap_low_field in [13.5]:
                    
                        # config_dict['tof_time'] = 50*ms
                # for det_mot in tqdm(np.arange(-25, -60, -5)):
                    for i in range(5):
                        config_dict['mtrap_hold_time'] = 800*ms
                        config_dict['tof_time'] = 8*ms
                        config_dict['rf_final_freq'] = rf_final_freq
                        # config_dict['rf_final_freq'] = 1.2
                        # config_dict['bias_b_field'] = .5
                        # config_dict['trap_low_field'] = trap_low_field
                        config_dict['bias_b_field'] = .59
                        config_dict['bias_ramp_time'] = bias_ramp_time
                        config_dict['spin_pol_time'] = spin_pol_time
                        config_dict['trap_b_field'] = 67
                        # config_dict['trap_b_field'] = 67
                        # config_dict['trap_b_field'] = 67
                        # config_dict['trap_b_field'] = trap_b_field
                        config_dict['det_img'] = -11
                        await single_shot(**config_dict)
                end_acq()
        