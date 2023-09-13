from lab_control.device import *
import numpy as np
from lab_control.core.config import config
from datetime import datetime 

config.offline = False
config.output_dir = rf'Q:\indium\data\2023\{datetime.now():%y%m%d}'
config.view = False
config.view_raw = False

TSChannel = TimeSequencer()
ts_in = TimeSequencerFPGA('192.168.107.194', 5555)

aio_326intensityServo = AIO(
    maxpd=np.array([33992.,     0.,     0.,     0.]),
    minpd=np.array([32906.,     0.,     0.,     0.]),
    port='COM51',
    ts_mapping={ramp:14, hsp:15}
)

# coil_servo = CoilServo(r'python Q:\indium\software\experimental_control_v2\ad5764_io\coil_vref\coil_vref_terminal_v6.py --non-interactive', ts_channel=16)

vco_controller = VCOController(r'python Q:\indium\software\experimental_control_v2\qNimble_vco_control\MOT_vco_sweep18V_v5\vco_terminal_v6.py --non-interactive', ts_channel=13)

# camera = CameraSolis()
