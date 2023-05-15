# This script is not expected to run alone
# This script is used to specify a time sequence described in python language
# This script is to be used with ts_csv_generator.py
# Edit line 86 in ts_csv_generator.py to something like: from this_sequence_name import *
# Run ts_csv_generator.py to generate a csv file that include the time-sequence described in this script

from unit import *
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

    @RawTS(channel=8, polarity=1)
    def om_zm_shutter():
        return [0]


if __name__ == '__main__':
    import asyncio
    from run_experiment import exec_actions, clean_up
    exp()
    asyncio.run(exec_actions())
    clean_up()

    exp(tof=2*ms)
    asyncio.run(exec_actions())
    clean_up()
