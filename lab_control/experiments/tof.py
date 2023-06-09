from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment
if __name__ == '__main__':
    from lab.sr_lab import *
# --- do not change anything above this line ---

from ..device.fname_gen.filename_gui import get_new_name


class Stage:
    pass


@Experiment(True, 'ts_sr')
def exp(cam_exposure=5*ms,
        load=4*s,
        mot_mag_delay=600*us,
        tof=4*ms,
        hs=1100):

    @Stage(duration=load)
    def load():
        @AIO0(action=ramp, channel=0)
        def repumper707():
            return [0, load - mot_mag_delay], [20, 20], [.95, .05]

        @AIO0(action=ramp, channel=1)
        def repumper679():
            return [0, load - mot_mag_delay], [20, 20], [.95, .05]

        @RawTS(channel=8, polarity=1)
        def om_zm_shutter():
            return [0, load]

        @AIO0(action=ramp, channel=2)
        def bfield():
            return [0, load], [2*ms, 500], [.60, .95]
        
        @AIO0(action=ramp, channel=3)
        def mot():
            return [0, load - mot_mag_delay], [20, 20], [.95, .05]

    @Stage(duration=tof)
    def TOF():
        pass

    @Stage(start=TOF.end)
    def take_pic():
        @AIO0(action=hsp, channel=0, hsp=hs)
        def repumper707():
            return [0, cam_exposure]

        @AIO0(action=hsp, channel=1, hsp=hs)
        def repumper679():
            return [0, cam_exposure]

        @AIO0(action=hsp, channel=3, hsp=hs)
        def mot():
            return [0, 0cam_exposure]

    @AndorCamera(
        action=external_start,
        spooling=True,
        spool_func=get_new_name,
        kcc=50*ms, nc=5,
        exposure_time=1*ms,
        first_image_at=tof+load-50*ms*3)
    def camera():
        return []


async def main():
    for tof in [1, ]:
        await exp(tof=tof*ms)