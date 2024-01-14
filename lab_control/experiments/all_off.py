from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine, acquisition
if __name__ == '__main__':
    from ..lab.in_lab import *
# --- do not change anything above this line ---

import numpy as np
from lab_control.core.config import config
# from ..lab.in_lab import start_acq, end_acq

@acquisition()
@Experiment(True, 'ts_in', 'remote_config')
def main():
    
    odt_setpoint = 1500
    odt_intensity = 0.97
    # det_mot = -52
    det_mot = -40
    det_ramp = 3000
    b_field = 43
    mot_intensity = 0.97

    @vco_controller()
    def vco_651_trig():
        ''' move to MOT detuning '''
        return [0], [det_ramp], [det_mot]
    
    @aio_326intensityServo(channel=0, action=ramp)
    def intensity326():
        return [0], [20], [mot_intensity]
    
    @TSChannel(channel=8)
    def zm_shutter():
        ''' turn on 326 beam for zm '''
        return []

    @TSChannel(channel=11, init_state=1)
    def mot_shutter():
        return []
    
    @TSChannel(channel=27, init_state=1)
    def mot_xy_shutter():
        ''' turn on the shutter '''
        return [0]

    @TSChannel(channel=7, )
    def mot_aom():
        ''' turn on the MOT beam'''
        return []
    
    @TSChannel(channel=21)
    def odt():
        ''' odt on '''
        return [0]
    
    @aio_1064intensityServo(action=hsp, channel=0)
    def odt_hsp():
        return [0], [odt_setpoint]

    @aio_1064intensityServo(action=ramp, channel=0)
    def odt_servo():
        return [0], [20], [odt_intensity]

    @TSChannel(channel=5)
    def field_unlock():
        ''' engage coil servo '''
        return [100000, 101000, ]

    @TSChannel(channel=1)
    def igbt0():
        return []
    
    @TSChannel(channel=3)
    def igbt3n4():
        return [0]

    @coil_servo
    def coil_vref():
        return [0], [200], [0]
    
    @aio_zcompServo(channel=0, action=ramp)
    def z_comp_coil_ramp():
        return [0,], [200], [.615]
    @aio_zcompServo(channel=1, action=ramp)
    def comp2_coil_ramp():
        return [0,], [200], [.538]
    @TSChannel(channel=19)
    def aom_rf_switch_410_451():
        ''' turn on repumpers '''
        return []
    
    @TSChannel(channel=20)
    def aom_410_master():
        return []

    # @TSChannel(channel=26, init_state=0 )
    # def mot_410_shutter():
    #     """ turn off 410 """
    #     return []
    
    # @TSChannel(channel=29, init_state=0)
    # def mot_451_shutter():
    #     """ turn off 451 """
    #     return []
    
    @TSChannel(channel=26, init_state=1)
    def mot_410_shutter():
        """ turn off 410 """
        return []
    
    @TSChannel(channel=29, init_state=1)
    def mot_451_shutter():
        """ turn off 451 """
        return []
    @TSChannel(channel=6, init_state=1)
    def zm_rp_shutter():
        ''' turn on zeeman repumpers '''
        return []
    
    
    @TSChannel(channel=35, init_state=1)
    def stirap_410():
        return []
    
    @TSChannel(channel=33, init_state=1)
    def aom_451_34():
        return []
    
    @TSChannel(channel=39, init_state=1)
    def stirap_410_shutter():
        ''' turn on zeeman repumpers '''
        return []