from lab_control.device import *
import numpy as np
from lab_control.core.config import config
from datetime import datetime 
from lab_control.remote.remote import to_in_desktop2, to_sr_remote, to_in_remote

config.offline = False
config.output_dir = rf'Q:\indium\data\2023\{datetime.now():%y%m%d}'
print(f'[INFO] Output directory is {config.output_dir}. ')
config.view = False
config.view_raw = False

# devices 
TSChannel = TimeSequencer()
ts_in = TimeSequencerFPGA('192.168.107.194', 5555)

aio_326intensityServo = AIO(
    maxpd=np.array([34150.,     0.,     0.,     0.]),
    minpd=np.array([33080.,     0.,     0.,     0.]),
    port='COM51',
    ts_mapping={ramp:14, hsp:15}
)

# aio_1064intensityServo = AIO(
#     maxpd=np.array([34400.,     0.,     0.,     0.]),
#     minpd=np.array([32903.,     0.,     0.,     0.]),
#     port='COM18',
#     ts_mapping={ramp:20, hsp:21}
# )
# missing intensity servo for repumpers 
# aio_410451Servo = AIO()

coil_servo = CoilServo(r'python Q:\indium\software\experimental_control_v2\ad5764_io\coil_vref\coil_vref_terminal_v6.py --non-interactive', ts_channel=16)

vco_controller = VCOController(r'python Q:\indium\software\experimental_control_v2\qNimble_vco_control\MOT_vco_sweep18V_v5\vco_terminal_v6.py --non-interactive', ts_channel=13)

remote_sim_control = to_in_desktop2.conn.modules.lab_control.device.fname_gen.EMCCD_simControl
# sr_wlm = WaveLengthMeterLockMonitor(
#     to_sr_remote.conn.modules.lab_control.device.wlm_lock.check_okay(
#         target_wavelength = {1: 651.40401, 4: 651.40416}
#     )
# )
# in_wlm = WaveLengthMeterLockMonitor(
#     to_in_remote.conn.modules.lab_control.device.wlm_lock.check_okay(
#         target_wavelength = {
#             1: 410.29190, 2: 451.25389, 
#             3: 451.25322, 4: 410.28541, 
#             5: 410.29203, 6: 410.28551, 
#             7: 451.25330, 8: 451.25400
#         }
#     )
# )
start_acq = remote_sim_control.action_changeFilenameAndStartCamAcq
end_acq =  remote_sim_control.action_StopCamAcq  
