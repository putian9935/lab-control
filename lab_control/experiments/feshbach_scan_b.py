from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, inject_lab_into_function
if __name__ == '__main__':
    from ..lab.in_lab import *
# --- do not change anything above this line ---

import numpy as np
from lab_control.core.config import config
# from ..lab.in_lab import start_acq, end_acq
prepare_time = 100*ms

from functools import partial

@Experiment(True, 'ts_in')
def single_shot(
    cool_mot_time=3.5*ms,
    tof_time=2.5*ms,
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
    odt_start_time=0,
    blast_duration=5*ms, 
    det_scan=-60,
    odt_high=.96,
    # feshbach 
    feshbach_b_field=0.1, 
    exposure_time=200*us,
    shutdown='fast',
    comment='',
):
    @TSChannel(channel=3, init_state=1)
    def igbt3n4():
        return []

    from .common_stages import prepare
    
    Stage(duration=prepare_time)(partial(inject_lab_into_function(prepare), prepare_time,))
    
    @Stage(duration=2*s)
    def load_mot():
        ''' MOT loading  '''
        @TSChannel(channel=24)
        def cmos_camera():
            return [1*s, 1*s+2*ms]

    @Stage(duration=cool_mot_time+100*us)
    def cool_mot():
        """ ramp to the correct low value """
        @TSChannel(channel=8)
        def zm_shutter():
            ''' turn off the shutter '''
            return [0]

        @TSChannel(channel=6)
        def zm_rp_shutter():
            return [-1*ms]

        @vco_controller()
        def vco_651_trig():
            return [0], [det_ramp], [det_low]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [0], [intensity_ramp], [intensity_low]

        @coil_servo()
        def coil_vref():
            return [0], [2000], [b_field_low]
        #  410/451 servo???

        
    @Stage(duration=odt_load_time)
    def load_odt():
        ''' Load atoms from cool mot into odt '''
        @aio_1064intensityServo(action=ramp, channel=0)
        def odt_ramp():
            ''' hold atoms '''
            return [0], [odt_ramp_time,], [odt_high,]
    
        @TSChannel(channel=20, init_state=1)
        def aom_410_master():
            # shut off 410 slave to let atoms decay to ground state
            return [odt_load_time+100-shutoff_410]
        
        @aio_326intensityServo(action=ramp, channel=0)
        def intensity326():
            ''' hold atoms '''
            return [odt_load_time-odt_load_mot_time-100], [odt_load_mot_time,], [0.03,]
        
    @Stage(duration=odt_hold_time, start_at=load_odt.end)
    def hold_odt():
        if shutdown == 'fast':
            @TSChannel(channel=1)
            def igbt0():
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
            
            @coil_servo()
            def coil_vref():
                return [0, 150, 400], [150, 300, 300], [40,25, -3]
            
        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            ''' shutdown the MOT beam,'''
            return [-100*us]
            # return [-100*us, odt_hold_time-mot_blast, odt_hold_time]
        
        @TSChannel(channel=11)
        def mot_shutter():
            return [-1.7*ms]

        @aio_326intensityServo(channel=0, action=hsp)
        def intensity326_disable():
            ''' disable intensity servo, constant dac output'''
            return [0], [32767+1100]

        @TSChannel(channel=19, init_state=1)
        def aom_rf_switch_410_451():
            ''' turn off repumpers '''
            return [0]
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [5*ms, odt_hold_time-5*ms], [1*ms, 1*ms], [feshbach_b_field, .615]
        
        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [10*ms], [det_ramp], [det_img]
        
        
        
    @Stage(duration=tof_time, start_at=hold_odt.end)
    def tof():
        @TSChannel(channel=10, action=pulse)
        def emccd_trig():
            return [tof_time - 2*ms]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [tof_time - 2*ms], [20], [intensity_high]
        
        @TSChannel(channel=21, )
        def odt():
            ''' free fall atoms '''
            return [0]
        
        @aio_1064intensityServo(action=hsp, channel=0)
        def odt_hsp():
            return [0], [0]

    @Stage(duration=exposure_time)
    def exposure():
        @TSChannel(channel=11, init_state=1)
        def mot_shutter():
            return [-1.7*ms]
        
        @TSChannel(channel=7)
        def mot_aom():
            ''' shine the MOT beam '''
            return [0, exposure_time]

        @TSChannel(channel=19)
        def aom_rf_switch_410_451():
            ''' shine repumpers '''
            return [0, exposure_time]
        
        @TSChannel(channel=20)
        def aom_410_master():
            return [0, exposure_time]
        
        @TSChannel(channel=24)
        def cmos_camera():
            return [-50, 500]

    @Stage(start_at=tof.end + 100*ms, duration=50*ms)
    def cleanup1():
        @TSChannel(channel=1)
        def igbt0():
            ''' bring back the magnetic field '''
            return [0]

        @aio_326intensityServo(channel=0, action=hsp)
        def intensity326_disable():
            ''' enable intensity servo '''
            return [0], []

        @coil_servo()
        def coil_vref():
            return [0], [2000], [b_field_mot]


    @Stage()
    def background():
        @TSChannel(channel=10, action=pulse)
        def emccd_trig():
            return [0]


        @TSChannel(channel=7)
        def mot_aom():
            ''' turn on the MOT beam'''
            return [2*ms, 2*ms+exposure_time]


        @TSChannel(channel=19)
        def aom_rf_switch_410_451():
            ''' turn on repumpers '''
            return [2*ms, 2*ms+exposure_time]

        @TSChannel(channel=20)
        def aom_410_master():
            return [2*ms, 2*ms+exposure_time]

    @Stage(start_at=background.end+50*ms)
    def cleanup2():        
        @TSChannel(channel=21)
        def odt():
            ''' odt on '''
            return [0]
        
        @aio_1064intensityServo(action=hsp, channel=0)
        def odt_hsp():
            return [0], []
        
        @TSChannel(channel=11)
        def mot_shutter():
            return [0]

        @TSChannel(channel=5)
        def field_unlock():
            ''' engage coil servo '''
            return [0]

        @TSChannel(channel=7)
        def mot_aom():
            ''' turn on the MOT beam'''
            return [0]

        @vco_controller()
        def vco_651_trig():
            ''' move to MOT detuning '''
            return [0], [det_ramp], [det_mot]

        @TSChannel(channel=19)
        def aom_rf_switch_410_451():
            ''' turn on repumpers '''
            return [0]

        @TSChannel(channel=20)
        def aom_410_master():
            return [0]

        @TSChannel(channel=6)
        def zm_rp_shutter():
            ''' turn on zeeman repumpers '''
            return [0]
import asyncio  
@inject_lab_into_coroutine
async def main():
    config_dict = {
        'cool_mot_time': 5*ms,
        'tof_time': 4*ms,
        # vco detuning
        # 'det_mot': 40,
        # 'det_low': 190,
        'det_mot': -60,
        'det_low': -170,
        'det_ramp': 3*ms,
        'det_img': -11,
        # 326 intensity
        'intensity_high': .95,
        'intensity_low': .95,
        # 'intensity_high': .7,
        # 'intensity_low': .7,
        'intensity_ramp': 1500*us,
        # b-field
        'b_field_mot': 45,
        'b_field_low': 45,
        # odt 
        'shutoff_410': 0*ms,
        # 'shutoff_410': 1*ms,
        'odt_ramp_time': 3000,
        'odt_hold_time': 75*ms, 
        'odt_load_time': 3000, 
        'odt_load_mot_time': 1, 
        'odt_start_time': -1000*us,
        'odt_high': 0.97,  
        'blast_duration':15*ms, 
        'det_scan':-60,
        # SG experiment 
        'sg_field':0, 
        # 'b_field_mot': 34,
        # 'b_field_low': 34,
        'feshbach_b_field':.615,
        'exposure_time': 500*us,
        'shutdown':'fast',
        'comment':'delay turn on feshbach b field'
    }
    config.update_cnt()
    start_acq(config.gen_fname_from_dict(config_dict)) 
    for _ in range(8):  
        for feshbach_b_field in np.arange(.42, .8, .003):
            config_dict['feshbach_b_field'] = feshbach_b_field
            await single_shot(**config_dict)
    end_acq()
