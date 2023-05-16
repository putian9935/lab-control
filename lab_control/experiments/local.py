from ..core.util.unit import *
from ..core.experiment import Experiment
if __name__ == '__main__':
    from ..lab.offline_lab_remote import *
# --- do not change anything above this line ---


@Experiment()
def main():
    @RawTS(channel=8, polarity=0)
    def om_zm_shutter():
        return []
