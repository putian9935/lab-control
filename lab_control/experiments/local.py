from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment
from lab_control.core.stage import Stage
if __name__ == '__main__':
    from ..lab.offline_lab import *
# --- do not change anything above this line ---

@Experiment()
def main():
    @Stage(start_at=2, duration=7)
    def load():
        @RawTS(channel=8, polarity=0)
        def om_zm_shutter():
            return [1,2,3,4,]
        @AIO0(ramp, channel=0)
        def repumper():
            return [0, 200], [30, 20], [.9, .1]

    @Stage(start_at=2*ms, duration=700)
    def wait():
        @RawTS(pulse, channel=9, polarity=0)
        def om_zm_shutter():
            return [1,2,3,4,]
        @RawTS(channel=8, polarity=0)
        def om_zm_shutter():
            return [-100,200]
             
    @Stage(start_at=wait.end)
    def measure():
        @RawTS(channel=8, polarity=0)
        def om_zm_shutter():
            return [4,500]
        @AIO0(hsp, channel=0, hsp=1100)
        def repumper():
            return [0, 200]
        @AIO0(ramp, channel=0)
        def repumper():
            return [0, 200], [30, 20], [.3, .0]
        