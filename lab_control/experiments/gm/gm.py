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
        return [-10]
    @TSChannel(channel=37, init_state=1)
    def aom_451_master():
        return [-10,]
    @TSChannel(channel=36, init_state=1)
    def aom_410_slave():
        return [-10,]
    @TSChannel(channel=20, init_state=1)
    def aom_410_master():
        return [-10,]

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
    gm_time=3.5*ms,
    cool_mot_time=4.2*ms,
    tof_time=2.5*ms,
    # vco detuning
    det_mot=40,
    det_low=150,
    det_ramp=1.5*ms,
    det_img=-11,
    det_gm=-900,
    det_raman=1753, 
    sb_power=+1,
    # 326 intensity
    intensity_high=.85,
    intensity_low=.45,
    rp_intensity_low=0.1,
    intensity_ramp=1500*us,
    # b-field
    b_field_mot=34,
    b_field_low=34,
    bef_mw_time=4*ms,
    bias_b_field = 0.615,
    bias_b_field2 = 0.594,
    bias_b_field1 = 0.488,
    odt_high=.96,
    exposure_time=200*us,
    exposure_intensity = .97,
    shutdown='fast',
    take_background = False,
    comment='',
):
    
    valon_synth_56.freq = det_raman
    valon_synth_56.power = sb_power
    
    @TSChannel(channel=3, init_state=1)
    def unused3():
        return []

    from ..common_stages import prepare, load_mot, cool_mot, cleanup1, background, cleanup2 
    everything = dict(globals(), **locals())
    prepare = Stage(duration=prepare_time+.1*s)(prepare, everything)

    load_mot = Stage(duration=load_mot_time)(load_mot,everything)
        
    # @Stage(duration=6000)
    @Stage(duration=bef_mw_time)
    def shutdown():
        turn_off_repumpers()
        # rp_intensity(0.01)

        @TSChannel(channel=8)
        def zm_shutter():
            ''' turn off the shutter '''
            return [0]

        @TSChannel(channel=6)
        def zm_rp_shutter():
            return [-1*ms]

        @aio_zcompServo(channel=1, action=ramp)
        def comp2_coil_ramp():
            return [1*ms], [1*ms], [bias_b_field2]

        @comp_coil1
        def _():
            return [1*ms], [1*ms], [bias_b_field1]
            
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [1*ms], [1*ms], [0.675]
        
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
    
        @vco_controller()
        def vco_651_trig():
            return [0*ms], [2.8*ms], [det_gm]
        

    @Stage(duration=gm_time)
    def gm():
        
        @TSChannel(channel=56, action=pulse)
        def test_trig():
            return [0]

        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            ''' on the MOT beam,'''
            return [0, gm_time]

        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [-500,0, ], [1, 2,], [-0.01, intensity_low]

        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            # ramp z-comp coil to 5G = 35373 DAC number
            return [0*ms], [3*ms], [0.655] # best value for 6ms after shutdown
        
        @gm_switch
        def _():
            return [0, gm_time]

        @TSChannel(channel=36, init_state=1)
        def aom_410_slave():
            return [0,gm_time]
        @TSChannel(channel=20, init_state=1)
        def aom_410_master():
            return [0,gm_time]
        
    
    @Stage(duration=exposure_time, start_at=gm.end+tof_time)
    def exposure():
        @vco_controller()
        def vco_651_trig():
            ''' move to on-resonance '''
            return [-6*ms], [4.5*ms], [det_img]
        @TSChannel(channel=10, action=pulse)
        def emccd_trig():
            return [-2*ms]

        rp_intensity(0.9)
        @aio_326intensityServo(channel=0, action=ramp)
        def intensity326():
            return [-2*ms], [20], [intensity_high]

            
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
        'gm_time': 4.2*ms,
        'tof_time': 6.6*ms,
        # vco detuning
        'det_mot': -40,
        'det_low': -90,
        # 'det_low': -170,
        'det_img': -6, 
        'det_ramp': 4.5*ms,
        # 326 intensity
        'intensity_high': 0.97,
        'intensity_low': 0.2,
        'rp_intensity_low':0.1,
        # 'intensity_high': .7,
        # 'intensity_low': .7,
        'intensity_ramp': 1500*us,
        # b-field
        'b_field_mot': 43,
        'b_field_low': 48,
        'exposure_time': 200*us, 
        'exposure_intensity': .97,
        'take_background':False
    }

    remote_config.update_cnt()
    await at_acq_start()
    from tqdm import tqdm 
    end_acq()
    
    for _ in range(80):
        config_dict['bias_b_field1'] = .482
        config_dict['bias_b_field2'] = .508
        fname = remote_config.gen_fname_from_dict(config_dict)
        
        # for sb_power in tqdm(np.arange(-2, 8)):
        for det_gm in tqdm(np.arange(-1090, -980, 5.5)):
            start_acq(fname)
            for det_raman in tqdm(np.arange(1751.7,1756.2,.12)):
        # for bias_b_field in tqdm(np.arange(.64,.66,.002)):
        # for gm_time in np.arange(.5,5,.5)*ms:
        # for _ in range(10000):
        # for gmt in [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 7000, 10*ms]:
                for tof_time in np.arange(6,20,3)*ms:
                    for _ in range(5):
                        config_dict['bef_mw_time'] = 3500
                        config_dict['bias_b_field'] = .67
                        config_dict['gm_time'] = 5*ms
                        config_dict['sb_power'] = +4
                        config_dict['det_raman'] = 1752.70
                        config_dict['det_gm'] = -1065
                        config_dict['tof_time'] = tof_time
                        config_dict['intensity_low'] = .9
                        await single_shot(**config_dict)
            end_acq()