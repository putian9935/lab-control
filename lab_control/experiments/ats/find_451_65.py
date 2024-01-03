from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, inject_lab_into_function, inject_dict_into_function, at_acq_end, at_acq_start
from functools import partial
if __name__ == '__main__':
    from ...lab.in_lab import *
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

@Experiment(True, 'ts_in', 'remote_config')
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
    exposure_time=200*us,
    shutdown='fast',
    comment='',
):
    @TSChannel(channel=3, init_state=1)
    def unused3():
        return []

    from ..common_stages import prepare, load_mot, cool_mot, cleanup1, cleanup2 
    everything = dict(globals(), **locals())
    prepare = Stage(duration=prepare_time+.1*s)(prepare, everything)

    load_mot = Stage(duration=load_mot_time)(load_mot,everything)
    cool_mot = Stage(duration=cool_mot_time+100*us)(cool_mot, everything)
    

    @Stage(duration=5000)
    # @Stage(duration=bef_mw_time)
    def shutdown():
        turn_off_repumpers() 

        @TSChannel(channel=56, action=pulse)
        def test_trig():
            return [0]

        # @aio_zcompServo(channel=0, action=ramp)
        # def z_comp_coil_ramp():
        #     # ramp z-comp coil to 5G = 35373 DAC number
        #     return [-6*ms], [4*ms], [bias_b_field]
        
        # @aio_zcompServo(channel=1, action=ramp)
        # def comp2_coil_ramp():
        #     return [-6*ms], [4*ms], [bias_b_field2]

        # @comp_coil1
        # def _():
        #     return [-6*ms], [4*ms], [bias_b_field1]
            
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

        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [0], [det_ramp], [det_img]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [0], [1], [0.01]

        # sweep 
        @TSChannel(channel=42, init_state=0)
        def offset_451_65_trig():
            return [0]
        
    @Stage(duration=1000+tof_time)
    def shine_451_65():
        @TSChannel(channel=30, init_state=0)
        def stirap_451():
            return [502,998]
        
        @TSChannel(channel=35, init_state=0)
        def stirap_410():
            return [500,1000]
        @TSChannel(channel=42, init_state=0)
        def offset_451_65_trig():
            return [1000]

        
    @Stage(duration=exposure_time)
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

        
    cleanup1 = Stage(start_at=shutdown.end + 100*ms, duration=50*ms)(inject_dict_into_function(cleanup1, everything))

    # cleanup2 = Stage(start_at=1250*ms)(partial(cleanup2,det_ramp, det_mot, ))
    cleanup2 = Stage(start_at=cleanup1.end+50*ms)(partial(cleanup2,det_ramp, det_mot, ))
  
@inject_lab_into_coroutine
async def main():
    config_dict = {
        'cool_mot_time': 4.2*ms,
        # 'cool_mot_time': 3.5*ms,
        'tof_time': 6.6*ms,
        # vco detuning
        # 'det_mot': 40,
        # 'det_low': 190,
        'det_mot': -40,
        'det_low': -170,
        # 'det_low': -90,
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
        'b_field_low': 48,
        # 'b_field_mot': 34,
        # 'b_field_low': 34,
        'exposure_time': 500*us, 
    }

    remote_config.update_cnt()
    await at_acq_start()
    import pyvisa as visa   
    rm = visa.ResourceManager()
    inst = rm.open_resource(device_name, timeout=5000, chunk_size=40*1024)
    def write_aom_451_65_voltage(v):
        inst.write(f'SOUR2:VOLT:OFFS {v*10.:.3f}V')

    from tqdm import tqdm 
    end_acq()
    
    while True:
        start_acq(remote_config.gen_fname_from_dict(config_dict))

        for offset in tqdm(np.arange(0, 10,.5)):
            write_aom_451_65_voltage(offset)
            config_dict['tof_time'] = 1*ms
            await single_shot(**config_dict)

        end_acq()
