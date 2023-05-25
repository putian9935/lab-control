from lab_control.device import *
import numpy as np

TSChannel = TimeSequencer()
# ts_in = TimeSequencerFPGA('192.168.107.146', 5555)
ts_in = TimeSequencerFPGA('192.168.107.194', 5555)

aio_326intensityServo = AIO(
    minpd=np.array([32926.,     0.,     0.,     0.]),
    maxpd=np.array([33544.,     0.,     0.,     0.]),
    port='COM15',
    ts_mapping={ramp:14, hsp:15}
)

# fname_gen = FileNameGenerator()
