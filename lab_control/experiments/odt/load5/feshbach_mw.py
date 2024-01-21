from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, inject_lab_into_function, inject_dict_into_function, acquisition
from functools import partial
if __name__ == '__main__':
    from ..lab.in_lab import *
# --- do not change anything above this line ---

import numpy as np
import asyncio
from lab_control.core.config import config
# from ..lab.in_lab import start_acq, end_acq
prepare_time = 100*ms


@Experiment(True, 'ts_in', 'remote_config')
def single_shot(
    load_mot_time=1*s,
    cool_mot_time=3.5*ms,
    tof_time=2.5*ms,
    rp_intensity=.95,
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
    odt_blink_freq=3e3,
    odt_mw=.97, 
    odt_duty_cycle=0.8,
    bias_b_field=0.6477, 
    odt_start_time=0,
    trap_oscillation_period=1*ms,
    odt_high=.96,
    mw_freq=11409.7531, 
    exposure_time=200*us,
    shutdown='fast',
    take_background=False,
    total_atom = True
):
    @TSChannel(channel=3,)
    def igbt3n4():
        return [0]

    from ...common_stages import prepare, load_mot, cool_mot, cleanup1, background, cleanup2
    everything = dict(globals(), **locals())

    prepare = Stage(duration=prepare_time+.1*s)(prepare, everything)

    load_mot = Stage(duration=load_mot_time)(load_mot, everything)

    """edit cool MOT for blinking ODT"""
    @Stage(duration=odt_blink_time)
    def blink_ODT():
        """ combine cool mot and blink odt"""

        """ ramp MOT det to the correct low value """
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

        @aio_1064intensityServo(action=ramp, channel=0)
        def odt_ramp():
            ''' hold atoms '''
            return [0], [1], [0.97]

        @TSChannel(channel=47, init_state=1)
        def odt_mod():
            return [0, odt_blink_time]

        @TSChannel(channel=48, init_state=1)
        def mot_mod():
            return [0, odt_blink_time]

        @TSChannel(channel=56, action=pulse)
        def test_trig():
            return [0]
    
    @Stage(duration=odt_load_time)
    def load_odt():
        ''' Load atoms from cool mot into odt '''

        @TSChannel(channel=7, init_state=1)
        def mot_aom():
            return [0]
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
                return [0, 150, 400], [150, 300, 300], [40, 25, -3]

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
            return [50*ms,], [2000], [.504]

        @comp_coil1
        def _():
            return [50*ms,], [2000], [.482]
            
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            # before 0.596
            return [50*ms,], [2000], [bias_b_field]

        @aio_1064intensityServo(action=ramp, channel=0)
        def odt_ramp():
            ''' hold atoms '''
            return [-20,], [2*ms, ], [odt_high,]

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

    optical_pumping_time = 70
    optical_pumping_duration = 70
    optical_pumping_f_state = -4
    @Stage(duration=optical_pumping_duration, start_at=hold_odt.start+45*ms)
    def optical_pumping():
        """ shine 451: 6->5', 5->5', 4->5', 3->4'; shine 410: 5->5'"""
        @TSChannel(channel=21, )
        def odt():
            ''' free fall atoms '''
            return [-2, 78]

        # @TSChannel(channel=56, action=pulse)
        # def test_trig():
        #     return [0]

        if not optical_pumping_f_state == -5:
            @TSChannel(channel=36)
            def aom_410_slave():
                if optical_pumping_time == 0:
                    return []
                return [0, optical_pumping_time]

        if not optical_pumping_f_state == -4:
            @TSChannel(channel=20)
            def aom_410_master():
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
                if optical_pumping_time == 0:
                    return []
                return [0, optical_pumping_time]
        @TSChannel(channel=39, init_state=1)
        def stirap_410_shutter():
            '''  '''
            return [-60*ms, 3*ms]
        @TSChannel(channel=35,)
        def stirap_410():
            if optical_pumping_time == 0:
                return []
            return [0, optical_pumping_time]
        @TSChannel(channel=26)
        def mot_410_shutter():
            return [optical_pumping_time]
        @TSChannel(channel=29)
        def mot_451_shutter():
            return [optical_pumping_time]

    @Stage(start_at=hold_odt.end-10*ms)
    def mw():
        @aio_zcompServo(channel=0, action=ramp)
        def z_comp_coil_ramp():
            return [-30*ms,], [5*ms], [0.64]
        valon_synth.freq = mw_freq
        @mw_switch
        def _():
            return [0, 800]
            
        @aio_1064intensityServo(action=ramp, channel=0)
        def odt_ramp():
            ''' hold atoms '''
            return [-1*ms, 1*ms], [500, 500], [odt_mw,odt_high]
    @Stage(duration=tof_time, start_at=hold_odt.end)
    def tof():
        
        @TSChannel(channel=21, )
        def odt():
            ''' free fall atoms '''
            return [0]
        
        @TSChannel(channel=26)
        def mot_410_shutter():
            return [-3*ms]
        @TSChannel(channel=29)
        def mot_451_shutter():
            return [-3*ms]
            
        if total_atom:
            @TSChannel(channel=36)
            def aom_410_slave():
                # shut off 410 slave to let atoms decay to ground state
                return [200,800]
    
   

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

        @TSChannel(channel=24)
        def cmos_camera():
            return [-250, 500]

    cleanup1 = Stage(start_at=tof.end + 50*ms, duration=50 *
                     ms)(inject_dict_into_function(cleanup1, everything))


    cleanup2 = Stage(start_at=cleanup1.end+50 *
                     ms)(partial(cleanup2, det_ramp, det_mot, ))


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
        'b_field_low': 55.8,
        # 'b_field_low': 50.8,
        # 'b_field_low': 48.8,
        # odt
        'shutoff_410': 0*ms,
        'odt_ramp_time': 2000,
        # 'odt_hold_time':250*ms,
        'odt_hold_time': 150*ms,
        # 'odt_load_time': 8000,
        'odt_load_time': 3,
        # 'odt_load_time': 3000,
        'odt_load_mot_time': 1,
        'odt_start_time': -1000*us,
        'odt_blink_time': 12*ms,
        # 'odt_blink_time':12*ms,
        'odt_blink_freq': 3.3e3,
        'odt_duty_cycle': 0.8,
        'odt_high': 0.6,
        'exposure_time': 500*us,
        'shutdown': 'fast',
        'take_background': False,
        'total_atom': True,
    }
    from tqdm import tqdm
    remote_config.update_cnt()

    end_acq()
    async with acquisition():
        await odt_modulator.update_amplitude(0.0, .4)
        await mot_modulator.update_amplitude(0.0, .4)
        odt_duty_cycle = 79.34020482
        mot_duty_cycle = 18.51827331
        while True:
            modulate_freq=5.5
            await odt_modulator.update_frequency(modulate_freq)
            await mot_modulator.update_frequency(modulate_freq)
            await odt_modulator.update_delay(-400e-9)
            await mot_modulator.update_edge_time(5e-6)
            await odt_modulator.update_edge_time(5e-6)

            mot_width = 1 / (modulate_freq*1e3) * mot_duty_cycle * 1e-2
            await mot_modulator.update_width(mot_width)
            odt_width = 1 / (modulate_freq*1e3) * odt_duty_cycle * 1e-2
            await odt_modulator.update_width(odt_width)
            delay_pi = 1 / (modulate_freq*1e3) - mot_width
            delay = 0
            await mot_modulator.update_delay(delay_pi + delay*1e-6)

            start_acq(remote_config.gen_fname_from_dict(config_dict))
            # for offset in ([0]):
            for offset in (0.191*2*np.array([-1, -2])):
                for mw_freq in tqdm(np.arange(-.1, .1, .0015)+offset+11409.7531):
                    for total_atom in [True, ]:
                        for bias_b_field in [.55, 0.6647]:
                            config_dict['load_mot_time'] = 1.8*s
                            # config_dict['load_mot_time'] = 2*s
                            config_dict['mw_freq'] = mw_freq
                            config_dict['total_atom'] = total_atom
                            config_dict['bias_b_field'] = bias_b_field
                            config_dict['odt_mw'] = .97
                            config_dict['det_low'] = -40
                            config_dict['odt_hold_time'] = 0.5*s
                            config_dict['odt_high'] = 0.97
                            config_dict['odt_blink_time'] = 12*ms
                            await single_shot(**config_dict)
            end_acq()
    # no rp