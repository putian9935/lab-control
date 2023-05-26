from lab_control.device import *
import numpy as np
from lab_control.core.config import config
from datetime import datetime 

config.output_dir = rf'Q:\indium\data\2023\{datetime.now():%y%m%d}'
config.view_raw = True

TSChannel = TimeSequencer()
ts_in = TimeSequencerFPGA('192.168.107.194', 5555)

aio_326intensityServo = AIO(
    minpd=np.array([32926.,     0.,     0.,     0.]),
    maxpd=np.array([33544.,     0.,     0.,     0.]),
    port='COM15',
    ts_mapping={ramp:14, hsp:15}
)

camera = CameraSolis()
