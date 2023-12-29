from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, inject_lab_into_function, inject_dict_into_function, at_acq_end, at_acq_start
from functools import partial
if __name__ == '__main__':
    from ..lab.in_lab import *
# --- do not change anything above this line ---

import numpy as np
from lab_control.core.config import config
# from ..lab.in_lab import start_acq, end_acq
prepare_time = 100*ms


@Experiment(True, 'ts_in','remote_config')
def single_shot(
    load_mot_time=1*s, 
    cool_mot_time=3.5*ms,
    tof_time=2.5*ms,
    rp_intensity = .95,
    # vco detuning
    det_mot=40,
    det_low=140,
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
    odt_blink_time=5*ms,
    odt_blink_freq = 3e3,
    odt_duty_cycle = 0.8,

    odt_start_time=0,
    trap_oscillation_period=1*ms,
    odt_high=.96,
    exposure_time=200*us,
    shutdown='fast',
    take_background = False
):
    @TSChannel(channel=3, init_state=1)
    def igbt3n4():
        return []

    from .common_stages import prepare, load_mot, cool_mot, cleanup1, background, cleanup2 
    everything = dict(globals(), **locals())


    prepare = Stage(duration=prepare_time+.1*s)(prepare, everything)
       
    load_mot = Stage(duration=load_mot_time)(load_mot,everything)

    """edit cool MOT for blinking ODT"""
    @Stage(duration = odt_blink_time)
    def blink_ODT():
        """ combine cool mot and blink odt"""

        """ ramp MOT det to the correct low value """
        @TSChannel(channel=56, action=pulse)
        def test_trig():
            return [odt_blink_time]
        @TSChannel(channel=8)
        def zm_shutter():
            ''' turn off the shutter '''
            return [-1*ms]

        @TSChannel(channel=6)
        def zm_rp_shutter():
            return [-1*ms]

        @vco_controller()
        def vco_651_trig():
            return [0], [odt_blink_time], [det_low]

        # @aio_326intensityServo(channel=0, action=ramp)
        # def intensity326():
        #     return [-500], [intensity_ramp], [intensity_low]

        @coil_servo
        def coil_vref():
            return [0], [2000], [b_field_low]
        #  410/451 servo???

        blink_period = 1/odt_blink_freq*1e6
        # blink_step1 = np.arange(0,odt_blink_time, blink_period)
        blink_step1 = np.arange(odt_blink_time,0, -blink_period)
        blink_offset = blink_period*(1-odt_duty_cycle)
        blink_step2 = blink_step1-blink_offset
        blink_steps = list(np.sort(np.hstack([blink_step1, blink_step2])).astype(int))
        blink_step2_odt = blink_step1-blink_offset * .88
        blink_steps_odt = list(np.sort(np.hstack([blink_step1, blink_step2_odt])- 20).astype(int) )

        
        @aio_1064intensityServo(action=ramp, channel=0)
        def odt_ramp():
            ''' hold atoms '''
            ret = blink_steps_odt, [5]*(len(blink_steps_odt)), [-0.05, odt_high,] * (len(blink_step1) )
            return ret
        # @TSChannel(channel=21)
        # def odt():
        #     ''' blink the ODT beam,'''
        #     return [-1]+blink_steps +[blink_steps[-1]+1]

        @aio_326intensityServo(action=ramp, channel=0)
        def intensity326():
            ''' hold atoms '''
            print(len(blink_steps))
            return blink_steps, [5]*(len(blink_steps)), [0.95,-0.05, ] * (len(blink_step1) )

        # blink_steps = [0, blink_steps[-1]]
        @TSChannel(channel=19, init_state=1)
        def aom_rf_switch_410_451():
            ''' shine repumpers '''
            return  blink_steps
        
        @TSChannel(channel=37, init_state=1)
        def aom_451_master():
            ''' turn off repumpers '''
            return  blink_steps
        
        @TSChannel(channel=20, init_state=1)
        def aom_410_master():
            return  blink_steps
        
        
        @TSChannel(channel=36, init_state=1)
        def aom_410_slave():
            # shut off 410 slave to let atoms decay to ground state
            return  blink_steps
    print('451 34 is 451 repump 5->5')

    @Stage(duration=odt_load_time)
    def load_odt():
        ''' Load atoms from cool mot into odt '''
        
    @Stage(duration=6*ms)
    def shutdown_mot_coil():
        if shutdown == 'fast':
            @TSChannel(channel=1)
            def igbt0():
                ''' shutdown the magnetic field '''
                return [0]

            @TSChannel(channel=3)
            def igbt3n4():
                ''' shutdown the magnetic field '''
                return [0]

            @TSChannel(channel=5)
            def field_unlock():
                ''' disengage the coil servo '''
                return [0]
        else: 
            @TSChannel(channel=1)
            def igbt0():
                ''' shutdown the magnetic field '''
                return [700]

            @TSChannel(channel=5)
            def field_unlock():
                ''' disengage the coil servo '''
                return [700]
            
            @coil_servo
            def coil_vref():
                return [0, 150, 400], [150, 300, 300], [40,25, -3]
            
        @TSChannel(channel=20, init_state=1)
        def aom_410_master():
            return [1]
        
        @TSChannel(channel=37, init_state=1)
        def aom_451_master():
            ''' turn off repumpers '''
            return [1]
        
        @TSChannel(channel=36, init_state=1)
        def aom_410_slave():
            return [1]
        # @TSChannel(channel=33, )
        # def aom_451_34():
        #     return [1]

        @TSChannel(channel=19, init_state=1)
        def aom_rf_switch_410_451():
            ''' turn off repumpers '''
            return [1]
  
    @Stage(duration=odt_hold_time)
    def hold_odt():
        @aio_zcompServo(channel=1, action=ramp)
        def comp2_coil_ramp():
            return [20,], [200], [.578]
            # return [20,], [200], [.536]
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [20,], [200], [.596]
        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            return [-2]
        @aio_1064intensityServo(action=ramp, channel=0)
        def odt_ramp():
            ''' hold atoms '''
            return [-20,], [20, ], [odt_high,]
        
        # @aio_1064intensityServo(action=ramp, channel=0)
        # def odt_ramp():
        #     ''' hold atoms '''
        #     return [ 20], [ 100*ms], [0.7]
        # @aio_1064intensityServo(action=ramp, channel=0)
        # def odt_ramp():
        #     ''' hold atoms '''
        #     return [101*ms], [ 100*ms], [0.4]    
        
        # @aio_1064intensityServo(action=ramp, channel=0)
        # def odt_ramp():
        #     ''' hold atoms '''
        #     return [202*ms], [ 100*ms], [0.2]    
        # @aio_1064intensityServo(action=ramp, channel=0)
        # def odt_ramp():
        #     ''' hold atoms '''
        #     return [303*ms], [ 100*ms], [0.1]    
        @TSChannel(channel=11)
        def mot_shutter():
            return [-1.7*ms]
        @TSChannel(channel=27)
        def mot_xy_shutter():
            ''' turn off the shutter '''
            return [-1.7*ms]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [1*ms], [1], [-0.05]
     
    
        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [10*ms], [10*ms], [det_img]

    optical_pumping_time = 40
    optical_pumping_duration=50 
    optical_pumping_f_state=-4
    # @Stage(duration=optical_pumping_duration, start_at=hold_odt.start+10*ms) 
    # def optical_pumping():
    #     """ shine 451: 6->5', 5->5', 4->5', 3->4'; shine 410: 5->5'"""
    #     @TSChannel(channel=21, )
    #     def odt():
    #         ''' free fall atoms '''
    #         return [-2, 78]
        
    #     # @TSChannel(channel=56, action=pulse)
    #     # def test_trig():
    #     #     return [0]

    #     if not optical_pumping_f_state == -5:
    #         @TSChannel(channel=36)
    #         def aom_410_slave():
    #             if optical_pumping_time == 0:
    #                 return []
    #             return [0, optical_pumping_time]
            
    #     if not optical_pumping_f_state == -4:
    #         @TSChannel(channel=20)
    #         def aom_410_master():
    #             if optical_pumping_time == 0:
    #                 return []
    #             return [0, optical_pumping_time]
        
    #     if not optical_pumping_f_state == 6:
    #         @TSChannel(channel=30)
    #         def stirap_451():
    #             if optical_pumping_time == 0:
    #                 return []
    #             return [0, optical_pumping_time]
        

    #     if not optical_pumping_f_state == 4:
    #         @TSChannel(channel=19)
    #         def aom_rf_switch_410_451():
    #             ''' shine repumpers '''
    #             if optical_pumping_time == 0:
    #                 return []
    #             return [0, optical_pumping_time]
        
    #     if not optical_pumping_f_state == 5:
    #         @TSChannel(channel=37)
    #         def aom_451_master():
    #             ''' shine repumpers '''
    #             if optical_pumping_time == 0:
    #                 return []
    #             return [0, optical_pumping_time]
        
    #     if not optical_pumping_f_state == 3:
    #         @TSChannel(channel=33,)
    #         def aom_451_34():
    #             if optical_pumping_time == 0:
    #                 return []
    #             return [0, optical_pumping_time]
    #     @TSChannel(channel=39, init_state=1)
    #     def stirap_410_shutter():
    #         '''  '''
    #         return [-60*ms, 3*ms]
    #     @TSChannel(channel=35,)
    #     def stirap_410():
    #         if optical_pumping_time == 0:
    #             return []
    #         return [0, optical_pumping_time]
        
    @Stage(duration=tof_time, start_at=hold_odt.end)
    def tof():
        @TSChannel(channel=21, )
        def odt():
            ''' free fall atoms '''
            return [0]
        
        @aio_1064intensityServo(action=hsp, channel=0)
        def odt_hsp():
            return [0], [0]

        
        
    @Stage(duration=exposure_time)
    def exposure():
        @TSChannel(channel=10, action=pulse)
        def emccd_trig():
            return [-2*ms]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [0], [20], [0.97]
        

        @TSChannel(channel=11,)
        def mot_shutter():
            return [-1.7*ms]
        
        @TSChannel(channel=27)
        def mot_xy_shutter():
            return [-2*ms]
        @TSChannel(channel=7)
        def mot_aom():
            ''' shine the MOT beam '''
            return [0, exposure_time]

        @aio_326intensityServo(action=ramp, channel=0)
        def intensity326():
            ''' hold atoms '''
            return [0], [20], [intensity_high]

        @TSChannel(channel=19)
        def aom_rf_switch_410_451():
            ''' shine repumpers '''
            return [0, exposure_time]
        
        @TSChannel(channel=20)
        def aom_410_master():
            return [0, exposure_time]
        
        # @TSChannel(channel=35, )
        # def stirap_410():
        #     return [0, exposure_time]
    
        @TSChannel(channel=37)
        def aom_451_master():
            ''' turn off repumpers '''
            return [0, exposure_time]
        
        @TSChannel(channel=36)
        def aom_410_slave():
            # shut off 410 slave to let atoms decay to ground state
            return [0, exposure_time]
        # @TSChannel(channel=33, )
        # def aom_451_34():
        #     return [0, exposure_time]
        @TSChannel(channel=24)
        def cmos_camera():
            return [-250, 500]

    cleanup1 = Stage(start_at=tof.end + 100*ms, duration=50*ms)(inject_dict_into_function(cleanup1, everything))


    background = Stage()(inject_dict_into_function(background, everything))

    cleanup2 = Stage(start_at=background.end+50*ms)(partial(cleanup2,det_ramp, det_mot, ))
  
        
@inject_lab_into_coroutine
async def main():
    config_dict = {
        'cool_mot_time': 4.2*ms,
        'tof_time': 1*ms,
        # vco detuning
        'det_mot': -40,
        # 'det_low': -45,
        'det_low': -170,
        # 'det_low': -170,
        'det_ramp': 3*ms,
        # 'det_ramp': 8*ms,
        'det_img': -11,
        # 326 intensity
        'intensity_high': .97,
        'intensity_low': .95,
        # 'intensity_high': .7,
        # 'intensity_low': .7,
        'intensity_ramp': 1500*us,
        # 'intensity_ramp': 20500*us,
        # b-field
        'b_field_mot': 43,
        'b_field_low': 50.8,
        # 'b_field_low': 48.8,
        # odt 
        'shutoff_410': 0*ms,
        'odt_ramp_time': 2000,
        # 'odt_hold_time':250*ms, 
        'odt_hold_time':150*ms, 
        # 'odt_load_time': 8000, 
        'odt_load_time': 3, 
        # 'odt_load_time': 3000, 
        'odt_load_mot_time': 1, 
        'odt_start_time': -1000*us,
        'odt_blink_time':10*ms,
        # 'odt_blink_time':12*ms,
        'odt_blink_freq' : 3.3e3,
        'odt_duty_cycle' : 0.8,

        'odt_high': 0.6,  
        'trap_oscillation_period':1*ms,
        # SG experiment 
        'sg_field':0, 

        # 'b_field_mot': 34,
        # 'b_field_low': 34,
        'exposure_time': 500*us,
        'shutdown':'fast',
        'take_background': False,
    }
    remote_config.update_cnt()
    await at_acq_start()
    # config.gen_fname_from_dict(config_dict)
    # start_acq(config.gen_fname_from_dict(config_dict))
    # from tqdm import tqdm 
    # for odt_duty_cycle in tqdm(np.arange(.6, 1, .1)):
    #     for odt_blink_freq in np.arange(2, 3.5, .2)*1e3:
    #         for _ in range(6):
    #             config_dict['odt_duty_cycle'] = odt_duty_cycle
    #             config_dict['odt_blink_freq'] = odt_blink_freq
    #             await single_shot(**config_dict)
    while True:
        await at_acq_start()
        # for bk_time in np.arange(2,14,1)*ms:
        # for det_low in np.arange(-70, -200, -10):
        # for freq in np.arange(1.5,3.5,0.2)*1e3:
        #     print(bk_time)
        config_dict['det_low'] = -170
        config_dict['odt_hold_time'] = 150*ms
        config_dict['odt_blink_time'] = 5*ms
        config_dict['odt_high'] = .97
        # config_dict['odt_blink_freq'] = freq
        await single_shot(**config_dict)


    # end_acq()
    