from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, inject_lab_into_function, inject_dict_into_function, acquisition
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
    @TSChannel(channel=33, init_state=1)
    def aom_451_34():
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
def single_shot(
    load_mot_time=1*s, 
    pgc_time=3.5*ms,
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
    # odt 
    shutoff_410=1*ms,
    optical_pumping_time=0*us, 
    optical_pumping_duration=250*us, 
    optical_pumping_f_state=-4, 
    optical_pumping_time_410=0*us,
    mw_time=1*ms, 
    bias_b_field = 0.615,
    b_field_analyze=0.6647,
    b_field_purify=15, 
    op_time=1.5*ms, 
    depump_time=1*ms, 
    exposure_time=200*us,
    delay_ramp_to_analyze=8500,
    exposure_intensity = .97,
    shutdown='fast',
    take_background = False,
    mw_freq=11409.7531,
    comment='',
):
    @TSChannel(channel=3, init_state=1)
    def unused3():
        return []

    from ...common_stages import prepare, load_mot, cleanup1, background, cleanup2 
    everything = dict(globals(), **locals())
    prepare = Stage(duration=prepare_time+.1*s)(prepare, everything)

    load_mot = Stage(duration=load_mot_time)(load_mot,everything)
        
    @Stage(duration=3000)
    def shutdown():
        turn_off_repumpers()
        rp_intensity(rp_intensity_low)

        @TSChannel(channel=8)
        def zm_shutter():
            ''' turn off the shutter '''
            return [0]

        @TSChannel(channel=6)
        def zm_rp_shutter():
            return [0]
        
        @aio_zcompServo(channel=1, action=ramp)
        def comp2_coil_ramp():
            return [-4*ms], [1*ms], [.508]
            
        @comp_coil1
        def _():
            return [-4*ms], [1*ms], [.482]            

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

        @TSChannel(channel=27)
        def mot_xy_shutter():
            ''' turn off the shutter '''
            return [-1*ms]
        @TSChannel(channel=25)
        def mot_top_shutter():
            ''' turn off the shutter '''
            return [-1*ms]
        @TSChannel(channel=56, action=pulse)
        def test_trig():
            return [0]
        
        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [0], [4.2*ms], [-850]
            # return [0], [2.2*ms], [-850]

        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [0*ms], [2*ms], [0.15]

    @Stage(duration=op_time,)
    def optical_pumping():
        
        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            ''' on the MOT beam,'''
            return [0, op_time]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [-500,0], [1, 2], [-0.01, .9]
        
        @TSChannel(channel=19, init_state=1)
        def aom_rf_switch_410_451():
            ''' turn on repumpers '''
            return [0,op_time]
        @TSChannel(channel=20, init_state=1)
        def aom_410_master():
            return [0,op_time]
        @TSChannel(channel=37, init_state=1)
        def aom_451_master():
            return [0,op_time]
        @TSChannel(channel=36, init_state=1)
        def aom_410_slave():
            return [0,op_time]

    det_32=-150
    @Stage(duration=5.8*ms) 
    def ramp_up():
        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [10*ms], [4.8*ms], [-6]
               
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            # ramp z-comp coil to 5G = 35373 DAC number
            return [0], [100], [0.66]
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

    @Stage(duration=300*ms)
    def mtrap():
        @coil_servo
        def coil_vref():
            return [10*ms], [30*ms], [b_field_purify]
    
        # @aio_zcompServo(channel=0, action=ramp)
        # def z_comp_coil_ramp():
        #     return [50*ms], [200], [0.63]
        @coil_servo
        def coil_vref():
            return [260*ms], [30*ms], [48]
        
    @Stage(duration=8*ms)
    def shutdown_b(): 
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
        
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [100], [200], [0.55]
            # return [100], [200], [0.75]
    @Stage(duration=optical_pumping_duration) 
    def optical_pumping():
        
        if not optical_pumping_f_state == -5:
            @TSChannel(channel=36)
            def aom_410_slave():
                if optical_pumping_time == 0:
                    return []
                return [0, optical_pumping_time]
            
        
        if not optical_pumping_f_state == 6:
            @TSChannel(channel=30)
            def stirap_451():
                if optical_pumping_time == 0:
                    return []
                return [0, optical_pumping_time]
        

        if not optical_pumping_f_state == 4:
            @TSChannel(channel=19)
            def aom_rf_switch_410_451():
                ''' shine repumpers '''
                if optical_pumping_time == 0:
                    return []
                return [0, optical_pumping_time]
        
        if not optical_pumping_f_state == 5:
            @TSChannel(channel=37)
            def aom_451_master():
                ''' shine repumpers '''
                if optical_pumping_time == 0:
                    return []
                return [0, optical_pumping_time]
        
        if not optical_pumping_f_state == 3:
            @TSChannel(channel=33,)
            def aom_451_34():
                # return []
                if optical_pumping_time == 0:
                    return []
                return [0, optical_pumping_time]
                # return [0, optical_pumping_time_410]
            
        @TSChannel(channel=35, init_state=1)
        def stirap_410():
            if optical_pumping_time == 0:
                return []
            # return [0, optical_pumping_time]
            return [0, optical_pumping_time_410]
        
        @TSChannel(channel=39,init_state=0)
        def stirap_410_shutter():
            ''' 0 is on ''' 
            return [optical_pumping_time_410-2.2*ms]
            # return [optical_pumping_time_410-2.5*ms]

    
        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [-1*ms,], [20], [intensity_high]

            
        @TSChannel(channel=7)
        def mot_aom():
            ''' shine the MOT beam '''
            return [0, optical_pumping_time_410]
            
    @Stage(duration=1*ms)
    def ramp_to_analyze():
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [400], [500], [b_field_analyze]
            
    @Stage(duration=15000)
    def depump():
        @TSChannel(channel=35, init_state=1)
        def stirap_410():
            if depump_time == 0:
                return []
            return [0, depump_time]
            
        @TSChannel(channel=36)
        def aom_410_slave():
            if depump_time == 0:
                return []
            return [0, depump_time]
        
        @TSChannel(channel=37)
        def aom_451_master():
            ''' shine repumpers '''
            if depump_time == 0:
                return []
            return [0, depump_time]
        @TSChannel(channel=19)
        def aom_rf_switch_410_451():
            ''' shine repumpers '''
            if depump_time == 0:
                return []
            return [0, depump_time]
            
    @Stage(duration=exposure_time, )
    def exposure():
        
        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [-6*ms], [4.8*ms], [det_img]
        @TSChannel(channel=27)
        def mot_xy_shutter():
            ''' turn off the shutter '''
            return [-3*ms]
        @TSChannel(channel=25)
        def mot_top_shutter():
            ''' turn off the shutter '''
            return [-3*ms]
        
        @TSChannel(channel=10, action=pulse)
        def emccd_trig():
            return [-2*ms]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [-1*ms,], [20], [intensity_high]

            
        @TSChannel(channel=7)
        def mot_aom():
            ''' shine the MOT beam '''
            return [0, exposure_time]

        
    cleanup1 = Stage(start_at=exposure.end + 100*ms, duration=50*ms)(inject_dict_into_function(cleanup1, everything))


    # cleanup2 = Stage(start_at=1250*ms)(partial(cleanup2,det_ramp, det_mot, ))
    cleanup2 = Stage(start_at=cleanup1.end+50*ms)(partial(cleanup2,det_ramp, det_mot, ))
  
@inject_lab_into_coroutine
async def main():
    config_dict = {
        'pgc_time': 4.2*ms,
        # 'pgc_time': 3.5*ms,
        'tof_time': 6.6*ms,
        # vco detuning
        # 'det_mot': 40,
        # 'det_low': 190,
        'det_mot': -40,
        'det_low': -170,
        'det_img': -6, 
        'det_ramp': 5*ms,
        # 326 intensity
        'intensity_high': 0.97,
        'intensity_low': 0.2,
        'rp_intensity_low':0.1,
        # 'intensity_high': .7,
        # 'intensity_low': .7,
        'intensity_ramp': 1500*us,
        # b-field
        'b_field_mot': 43,
        'optical_pumping_time':200,
        'optical_pumping_duration':550,
        # 'b_field_mot': 34,
        'exposure_time': 500*us, 
        # 'exposure_time': 200*us, 
        'exposure_intensity': .97,
        'take_background':False
    }

    remote_config.update_cnt()
    from tqdm import tqdm 
    # end_acq()
    for _ in range(80):
        async with acquisition():
            # start_acq(remote_config.gen_fname_from_dict(config_dict))
            
            for depump_time in tqdm(np.arange(0, 15000, 1000)):
                for _ in range(6):
                    config_dict['bias_b_field'] = .66
                    config_dict['b_field_analyze'] = .55
                    config_dict['pgc_time'] = 5.4*ms
                    config_dict['intensity_low'] = .97
                    config_dict['rp_intensity_low'] = 0.2
                    config_dict['det_low'] = -200
                    config_dict['det_img'] = -6
                    # op_time for 326 
                    config_dict['op_time'] = 6.5*ms
                    config_dict['b_field_purify'] = 48
                    # optical_pumping_time for 410
                    config_dict['optical_pumping_time'] =  500+300+400+400+200+200
                    config_dict['optical_pumping_time_410'] = 1600
                    config_dict['depump_time'] = depump_time
                    await single_shot(**config_dict)
                    break 
                break 
            # end_acq()
