from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment
from lab_control.core.stage import Stage
if __name__ == '__main__':
    from ..lab.offline_lab import *
# --- do not change anything above this line ---

@Experiment()
def main():
    @Stage(start_at=2, duration=7)
    def stage1():
        @RawTS(channel=8, polarity=0)
        def om_zm_shutter():
            return [1,2,3,4,]
        
    @Stage()
    def stage3():
        @RawTS(channel=2, polarity=0)
        def om_zm_shutter():
            return [5,4]