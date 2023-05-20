from lab_control.core.util.unit import *
from lab_control.core.experiment import Experiment
if __name__ == '__main__':
    from ..lab.offline_lab import *
# --- do not change anything above this line ---


@Experiment()
def main():
    @sta
    @RawTS(channel=8, polarity=0)
    def om_zm_shutter():
        return []
