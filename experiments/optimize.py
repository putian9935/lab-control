from util.unit import *
if __name__ == '__main__':
    from lab.sr_lab import *
from core.experiment import Experiment


@Experiment(True, ts_sr)
def main():
    @AIO0(action=ramp, channel=0)
    def mot():
        return [0], [20], [.95]

    @AIO0(action=ramp, channel=1)
    def repump707():
        return [0], [20], [.95]

    @AIO0(action=ramp, channel=3)
    def repump707():
        return [0], [20], [.95]

    @AIO0(action=ramp, channel=2)
    def bfield():
        return [0], [2000], [.65]

    @RawTS(channel=8, polarity=0)
    def om_zm_shutter():
        return []
