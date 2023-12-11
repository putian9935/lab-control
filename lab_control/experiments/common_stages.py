from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment, Stage, inject_lab_into_coroutine
if __name__ == '__main__':
    from ..lab.in_lab import *


def prepare():
    @TSChannel(channel=8, init_state=0)
    def zm_shutter():
        ''' turn on 326 beam for zm '''
        return [0]

    @TSChannel(channel=11, init_state=1)
    def mot_shutter():
        return [prepare_time]

    @aio_1064intensityServo(action=ramp, channel=0)
    def odt_ramp():
        ''' turn off ODT during loading '''
        return [prepare_time-10*ms], [4*ms], [.02]
    
    @aio_1064intensityServo(action=ramp, channel=1)
    def odt_modulate():
        ''' turn off ODT during loading '''
        return [0], [1], [.5]
    
    @TSChannel(channel=21, init_state=1)
    def odt():
        ''' constant on '''
        return []

    # optimized for loading 
    @aio_zcompServo(channel=0, action=ramp)
    def z_comp_coil_ramp():
        """old MOT loading z direction b field"""
        return [0], [200], [.615]

    @aio_zcompServo(channel=1, action=ramp)
    def comp2_coil_ramp():
        """old MOT loading 1 direction b field"""
        # return [0,], [200], [.488]
        return [0,], [200], [.528]
    
    @comp_coil1
    def _():
        # return [0], [200], [.46]
        return [0], [200], [.488]
    # @aio_zcompServo(channel=0, action=ramp)
    # def z_comp_coil_ramp():
    #     """0 MOT loading z direction b field"""
    #     return [0], [200], [.60]
    # @aio_zcompServo(channel=1, action=ramp)
    # def comp2_coil_ramp():
    #     """0 MOT loading 1 direction b field"""
    #     return [0,], [200], [.584]
    
    @TSChannel(channel=35, init_state=1)
    def stirap_410():
        return []
    
    @TSChannel(channel=33, init_state=1)
    def aom_451_34():
        print('451 34 is 451 repump, do you want to edit common stages? ')
        return []
    
    @aio_326intensityServo(channel=0, action=ramp)
    def intensity326():
        return [0], [intensity_ramp], [intensity_high]
    
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
    
def load_mot():
    ''' MOT loading  '''
    @TSChannel(channel=24)
    def cmos_camera():
        return [load_mot_time-500, load_mot_time-200]

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

    @coil_servo
    def coil_vref():
        return [0], [2000], [b_field_low]
    #  410/451 servo???
    
def cleanup1():
    @TSChannel(channel=1)
    def igbt0():
        ''' bring back the magnetic field '''
        return [0]

    @coil_servo
    def coil_vref():
        return [0], [2000], [b_field_mot]

def background():
    if take_background:
        @TSChannel(channel=10, action=pulse)
        def emccd_trig():
            return [-2*ms]


    @TSChannel(channel=7)
    def mot_aom():
        ''' turn on the MOT beam'''
        return [2*ms, 2*ms+exposure_time]


    @TSChannel(channel=19)
    def aom_rf_switch_410_451():
        ''' turn on repumpers '''
        return [2*ms, 2*ms+exposure_time]


    @TSChannel(channel=37)
    def aom_451_master():
        ''' turn on repumpers '''
        return [2*ms, 2*ms+exposure_time]
    
    @TSChannel(channel=20)
    def aom_410_master():
        return [2*ms, 2*ms+exposure_time]
    
    @TSChannel(channel=35, )
    def stirap_410():
        return [2*ms, 2*ms+exposure_time]
    
    @TSChannel(channel=33, )
    def aom_451_34():
        return [2*ms, 2*ms+exposure_time]
    
    @TSChannel(channel=36)
    def aom_410_slave():
        return [2*ms, 2*ms+exposure_time]
    
def cleanup2(det_ramp, det_mot):
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

    @TSChannel(channel=36)
    def aom_410_slave():
        return [0]

    @TSChannel(channel=37)
    def aom_451_master():
        return [0]
    @TSChannel(channel=6)
    def zm_rp_shutter():
        ''' turn on zeeman repumpers '''
        return [0]
 
