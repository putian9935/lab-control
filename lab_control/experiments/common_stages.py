from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine
if __name__ == '__main__':
    from ..lab.in_lab import *


def prepare(prepare_time):
    @TSChannel(channel=8)
    def zm_shutter():
        ''' turn on 326 beam for zm '''
        return [0]

    @TSChannel(channel=27)
    def mot_xy_shutter():
        ''' turn on the shutter '''
        return [0]
    @TSChannel(channel=11, init_state=1)
    def mot_shutter():
        return [prepare_time]
    
    @aio_1064intensityServo(action=ramp, channel=0)
    def odt_ramp():
        ''' turn off ODT during loading '''
        return [0], [4*ms], [.02]
    
    @TSChannel(channel=21, init_state=1)
    def odt():
        ''' constant on '''
        return []
    
    @aio_zcompServo(channel=0, action=ramp)
    def z_comp_coil_ramp():
        return [0 ], [200], [.615]