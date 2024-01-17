from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, acquisition
if __name__ == '__main__':
    from ..lab.in_lab import *
# --- do not change anything above this line ---

import numpy as np
from lab_control.core.config import config
# from ..lab.in_lab import start_acq, end_acq

@Experiment(True, 'ts_in', 'remote_config')
def turn_on_all():
    
    odt_setpoint = 1500
    odt_intensity = 1.1
    # odt_intensity = 0.97
    # det_mot = -52
    det_mot = -40
    # det_mot = -40
    # det_mot = -70
    det_ramp = 3000
    b_field = 43
    mot_intensity = 0.97

    @vco_controller()
    def vco_651_trig():
        ''' move to MOT detuning '''
        return [0], [det_ramp], [det_mot]
    
    @aio_326intensityServo(channel=0, action=ramp)
    def intensity326():
        return [0], [20], [0.97]
        # return [0], [20], [mot_intensity]
    
    @TSChannel(channel=8)
    def zm_shutter():
        ''' turn on 326 beam for zm '''
        return [0]

    @TSChannel(channel=11, init_state=1)
    def mot_shutter():
        return [0]
    
    @TSChannel(channel=27, init_state=1)
    def mot_xy_shutter():
        ''' turn on the shutter '''
        return [0]

    @TSChannel(channel=34, init_state=0)
    def mot_z_shutter():
        ''' turn on the shutter '''
        return []
    
    @TSChannel(channel=7, init_state=1)
    def mot_aom():
        ''' turn on the MOT beam'''
        return []
    
    @TSChannel(channel=21)
    def odt():
        ''' odt on '''
        return [0]
    
    @TSChannel(pulse, channel=56)
    def test_trig():
        return [0]
    # @aio_1064intensityServo(action=hsp, channel=0)
    # def odt_hsp():
    #     return [0], [odt_setpoint]

    @aio_1064intensityServo(action=ramp, channel=0)
    def odt_servo():
        return [0], [20], [odt_intensity]

    @TSChannel(channel=5)
    def field_unlock():
        ''' engage coil servo '''
        return []

    @TSChannel(channel=1)
    def igbt0():
        return []
    
    @TSChannel(channel=3)
    def igbt3n4():
        return [0]

    @TSChannel(channel=2)
    def igbt1n2():
        return []
    @coil_servo
    def coil_vref():
        return [0], [200], [b_field]
    
    @aio_zcompServo(channel=0, action=ramp)
    def z_comp_coil_ramp():
        return [0,], [200], [.63]
    # @aio_zcompServo(channel=0, action=ramp)
    # def z_comp_coil_ramp():
    #     return [0,], [200], [.478]
    @aio_zcompServo(channel=1, action=ramp)
    def comp2_coil_ramp():
        return [0,], [200], [.528]
    @comp_coil1
    def _():
        return [0], [200], [.488]
    
    @TSChannel(channel=19)
    def aom_rf_switch_410_451():
        ''' turn on repumpers '''
        return [0]
    
    @TSChannel(channel=20)
    def aom_410_master():
        return [0]

    @TSChannel(channel=36)
    def aom_410_slave():
        return [0]
    @TSChannel(channel=6, init_state=1)
    def zm_rp_shutter():
        ''' turn on zeeman repumpers '''
        return [0]
    
    @TSChannel(channel=29, init_state=0)
    def mot_451():
        return []
    
    @TSChannel(channel=30, init_state=1)
    def stirap_451():
        return []
    
    @TSChannel(channel=35, init_state=0)
    def stirap_410():
        return []
    
    @TSChannel(channel=33, init_state=0)
    def aom_451_34():
        return []
    
    @TSChannel(channel=37, init_state=0)
    def aom_451_master():
        return [0]
    @TSChannel(channel=31, init_state=1)
    def absorption_aom():
        return [0]
    
    @mw_switch
    def _():
        return []
    
    @TSChannel(channel=26, init_state=0)
    def mot_410_shutter():
        ''' turn on zeeman repumpers '''
        return []
    @TSChannel(channel=39, init_state=0)
    def stirap_410_shutter():
        ''' turn on zeeman repumpers '''
        return []

    @aio_rp(channel=0, action=ramp)
    def intensity_410_master():
        return [0], [2], [.95]
    @aio_rp(channel=1, action=ramp)
    def intensity_410_slave():
        return [0], [2], [.95]
    @aio_rp(channel=2, action=ramp)
    def intensity_451_master():
        return [0], [2], [.95]
    @aio_rp(channel=3, action=ramp)
    def intensity_451_slave():
        return [0], [2], [.95]

    @TSChannel(channel=40, init_state=0)
    def offset_410_trig():
        return [1*s, 1.2*s,]
    
    @gm_switch
    def _():
        return []
    
    @TSChannel(channel=47, init_state=1)
    def odt_mod():
        return []
    
    @TSChannel(channel=48, init_state=1)
    def mot_mod():
        return []

@inject_lab_into_coroutine
async def main():
    async with acquisition():
        
        modulate_freq = 5.3
        odt_duty_cycle = 80
        odt_width = 1 / (modulate_freq*1e3) * odt_duty_cycle * 1e-2
        await odt_modulator.update_width(odt_width)
        await odt_modulator.update_delay(-400e-9)
        await mot_modulator.update_width(odt_width)
        await mot_modulator.update_delay(0)

        await turn_on_all()