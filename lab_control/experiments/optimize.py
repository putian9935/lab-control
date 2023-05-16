from ..core.util.unit import *
from ..core.experiment import Experiment
if __name__ == '__main__':
    from ..lab.sr_lab import *
# --- do not change anything above this line ---


@Experiment(True, ts_sr)
def main():
    @AIO0(action=ramp, channel=0)
    def repumper707():
        return [0], [20], [.95]

    @AIO0(action=ramp, channel=1)
    def repump679():
        return [0], [20], [.95]

    @AIO0(action=ramp, channel=3)
    def mot():
        return [0], [20], [.95]

    @AIO0(action=ramp, channel=2)
    def bfield():
        return [0], [2000], [.65]

    @RawTS(channel=8, polarity=0)
    def om_zm_shutter():
        return []
