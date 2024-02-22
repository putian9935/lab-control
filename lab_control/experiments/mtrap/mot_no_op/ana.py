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
    sg_field=35, 
    # odt 
    shutoff_410=1*ms,
    optical_pumping_time=0*us, 
    optical_pumping_duration=250*us, 
    optical_pumping_f_state=-4, 
    mw_time=1*ms, 
    bef_mw_time=4*ms,
    bias_b_field = 0.615,
    kick_field = 0.4,
    odt_high=.96,
    op_time=1.5*ms, 
    mt_hold_time = 200*ms,
    mt_hold_b_field = 30,
    exposure_time=200*us,
    exposure_intensity = .97,
    shutdown='fast',
    take_background = False,
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
    # @Stage(duration=bef_mw_time)
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
            return [0], [2*ms], [det_low]

        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [1*ms], [1*ms], [.675]
        
        @aio_zcompServo(channel=1, action=ramp)
        def comp2_coil_ramp():
            return [1*ms], [1*ms], [.504]
            
        @comp_coil1
        def _():
            return [1*ms], [1*ms], [.482]            

        @coil_servo
        def coil_vref():
            return [-5*ms], [2000], [48]
        # @TSChannel(channel=1)
        # def igbt0():
        #     ''' shutdown the magnetic field '''
        #     return [0]

        # @TSChannel(channel=3, init_state=1)
        # def unused3():
        #     return [0]
        
        # @TSChannel(channel=5)
        # def field_unlock():
        #     ''' disengage the coil servo '''
        #     return [0]

        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            ''' shutdown the MOT beam,'''
            return [-100*us]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [0], [1], [0.01]

    # @Stage(duration=pgc_time)
    # def pgc():
    #     @TSChannel(channel=56, action=pulse)
    #     def test_trig():
    #         return [0]

    #     @aio_zcompServo(channel=0, action=ramp)
    #     def z_comp_coil_ramp():
    #         # ramp z-comp coil to 5G = 35373 DAC number
    #         return [0*ms, 3*ms], [3*ms, 500], [0.66, .66] # best value for 6ms after shutdown
        
    #     @TSChannel(channel=7, init_state=1)
    #     def mot_aom():
    #         ''' on the MOT beam,'''
    #         return [0, pgc_time]

    #     @aio_326intensityServo(channel=0, action=ramp)
    #     def intensity326():
    #         return [-500,0], [1, 2], [-0.01, intensity_low]
        
    #     @aio_rp(channel=0, action=ramp)
    #     def intensity_410_master():
    #         return [-500,0], [1, 2], [-0.01, rp_intensity_low]
    #     @aio_rp(channel=1, action=ramp)
    #     def intensity_410_slave():
    #         return [-500,0], [1, 2], [-0.01, rp_intensity_low]
    #     @aio_rp(channel=2, action=ramp)
    #     def intensity_451_master():
    #         return [-500,0], [1, 2], [-0.01, rp_intensity_low]
    #     @aio_rp(channel=3, action=ramp)
    #     def intensity_451_slave():
    #         return [-500,0], [1, 2], [-0.01, rp_intensity_low]

    #     @TSChannel(channel=19, init_state=1)
    #     def aom_rf_switch_410_451():
    #         ''' turn on repumpers '''
    #         return [0, pgc_time]
    #     @TSChannel(channel=20, init_state=1)
    #     def aom_410_master():
    #         return [0,pgc_time]
    #     @TSChannel(channel=37, init_state=1)
    #     def aom_451_master():
    #         return [0,pgc_time]
    #     @TSChannel(channel=36, init_state=1)
    #     def aom_410_slave():
    #         return [0,pgc_time]

    #     @TSChannel(channel=27)
    #     def mot_xy_shutter():
    #         ''' turn off the shutter '''
    #         return [pgc_time]
    #     @TSChannel(channel=25)
    #     def mot_top_shutter():
    #         ''' turn off the shutter '''
    #         return [pgc_time]
        
    # @Stage(duration=2.5*ms) 
    # def ramp_down():
    #     @vco_controller()
    #     def vco_651_trig():
    #         ''' move to on-resonance '''
    #         return [0], [2.2*ms], [-850]
    
    # @Stage(duration=op_time,)
    # def optical_pumping():
    #     @aio_zcompServo(channel=0, action=ramp)
    #     def z_comp_coil_ramp():
    #         return [-2*ms], [2*ms], [0.45]
        
    #     @TSChannel(channel=7, init_state=1)
    #     def mot_aom():
    #         ''' on the MOT beam,'''
    #         return [0, op_time]

    #     @aio_326intensityServo(channel=0, action=ramp)
    #     def intensity326():
    #         return [-500,0], [1, 2], [-0.01, .9]
        
    #     @TSChannel(channel=19, init_state=1)
    #     def aom_rf_switch_410_451():
    #         ''' turn on repumpers '''
    #         return [0,op_time]
    #     @TSChannel(channel=20, init_state=1)
    #     def aom_410_master():
    #         return [0,op_time]
    #     @TSChannel(channel=37, init_state=1)
    #     def aom_451_master():
    #         return [0,op_time]
    #     @TSChannel(channel=36, init_state=1)
    #     def aom_410_slave():
    #         return [0,op_time]

    @Stage(duration=5.8*ms) 
    def ramp_up():
        @TSChannel(channel=56, action=pulse)
        def test_trig():
            return [0]
            
        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [10*ms], [4.8*ms], [det_img]
               
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            # ramp z-comp coil to 5G = 35373 DAC number
            return [0], [2*ms], [0.66]
        # @TSChannel(channel=1)
        # def igbt0():
        #     ''' shutdown the magnetic field '''
        #     return [0]

        # @TSChannel(channel=3, init_state=1)
        # def unused3():
        #     return [0]
        
        # @TSChannel(channel=5)
        # def field_unlock():
        #     ''' disengage the coil servo '''
        #     return [0]

        @coil_servo
        def coil_vref():
            return [0], [2000], [60]
    @Stage(duration=mt_hold_time)
    def mtrap():
        @coil_servo
        def coil_vref():
            return [20*ms], [50*ms], [mt_hold_b_field]
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
                # ramp z-comp coil to 5G = 35373 DAC number
                return [80*ms], [200], [kick_field]
            
    
    @Stage()
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
        
    @Stage(duration=exposure_time, start_at=shutdown_b.end+tof_time)
    def exposure():
        
        # @TSChannel(channel=27)
        # def mot_xy_shutter():
        #     ''' turn off the shutter '''
        #     return [-3*ms]
        # @TSChannel(channel=25)
        # def mot_top_shutter():
        #     ''' turn off the shutter '''
        #     return [-3*ms]
        
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
        # rp_intensity(0.9)
        # @TSChannel(channel=19, init_state=1)
        # def aom_rf_switch_410_451():
        #     ''' turn on repumpers '''
        #     return [0, exposure_time]
        # @TSChannel(channel=20, init_state=1)
        # def aom_410_master():
        #     return [0, exposure_time]
        # @TSChannel(channel=37, init_state=1)
        # def aom_451_master():
        #     return [0, exposure_time]
        # @TSChannel(channel=36, init_state=1)
        # def aom_410_slave():
        #     return [0, exposure_time]

    # print(f'kick is {kick_field}')
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
        'optical_pumping_time':500,
        'optical_pumping_duration':550,
        'mt_hold_time': 60*ms,
        'mt_hold_b_field': 40,
        'kick_field':0.63,
        # 'b_field_mot': 34,
        'exposure_time': 200*us, 
        'exposure_intensity': .97,
        'take_background':False
    }

    remote_config.update_cnt()
    await at_acq_start()
    from tqdm import tqdm 
    end_acq()
    
    for _ in range(80):
        # for bias_b_field in [.65, .6505, .651, .6515]:
        start_acq(remote_config.gen_fname_from_dict(config_dict))
        for mt_hold_b_field in tqdm(np.arange(10,38,0.2)):
            # for _ in range(6):
                config_dict['bef_mw_time'] = 6000
                config_dict['bias_b_field'] = .66
                # for tof_time in np.arange(5, 26, 1)*ms:
                # for rp_intensity_low in np.arange(0.05, .8, .05):
                # for intensity_low in np.arange(0.05, .8, .05):
                # for det_low in np.arange(-170, -280, -5):
                # for pgc_time in np.arange(0.1, 3, .1)*ms:
                config_dict['pgc_time'] = 5.4*ms
                config_dict['tof_time'] =2*ms
                config_dict['intensity_low'] = .97
                config_dict['rp_intensity_low'] = 0.2
                config_dict['det_low'] = -200
                config_dict['det_img'] = -6
                config_dict['op_time'] = 5*ms
                config_dict['mt_hold_time'] = 300*ms
                config_dict['mt_hold_b_field'] = mt_hold_b_field
                # config_dict['op_time'] = op_time
                await single_shot(**config_dict)
        end_acq()