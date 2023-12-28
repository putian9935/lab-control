from lab_control.device import *
import numpy as np
from lab_control.core.config import config
from datetime import datetime 
from lab_control.remote.remote import to_in_helm # , to_sr_remote, to_in_remote

config.offline = False
config.view = False
config.view_raw = False

# devices 
TSChannel = TimeSequencer()
ts_in = TimeSequencerFPGA('192.168.107.194', 5555)

aio_326intensityServo = AIO(
    maxpd=np.array([33790,    0.,     0.,     0.]),
    minpd=np.array([32817.,     0.,     0.,     0.]),
    port='COM20',
    ts_mapping={ramp:14, hsp:15}
)

# hsp is disabled for channel 1
# 0.5 is VCO@80MHz 
aio_1064intensityServo = AIO(
    maxpd=np.array([58900.,    19065.,     0.,     0.]),
    minpd=np.array([33640.,    17445.,     0.,     0.]),
    port='COM21',
    ts_mapping={ramp:22, hsp:23}
)

# NOTE: 42000 = 3.0V on output = 2.0A of current
#       34300 = 390mV on output = 260mA of current
# do not use ramp, only hsp
aio_zcompServo = AIO(
    maxpd=np.array([42000.,     42000.,     42000.,     0.]),
    minpd=np.array([22000.,     22000.,     22000.,     0.]),
    port='COM24',
    ts_mapping={ramp:28, hsp:27}
)

comp_coil1 = aio_zcompServo(action=ramp, channel=2)

# missing intensity servo for repumpers 
aio_rp = AIO(
    port='COM27',
    # r'python C:\Users\indium_desktop1\Desktop\rp_servo\terminal\terminal_vanilla.py --non-interactive',
    maxpd=np.array([33691., 33451., 33046., 34412.]),
    minpd=np.array([32810., 32777., 32940., 32846.]),
    ts_mapping={ramp:17, hsp:18},
    # name='aio_rp'
)

aio_coil_vref = AIO(
    port='COM14',
    # r'python C:\Users\indium_desktop1\Desktop\rp_servo\terminal\terminal_vanilla.py --non-interactive',
    maxpd=np.array([327.68, 0, 0, 0,]),
    minpd=np.array([0, 0, 0, 0]),
    ts_mapping={ramp:16},
)
coil_servo = aio_coil_vref(action=ramp, channel=0)

# coil_servo = CoilServo(r'python Q:\indium\software\experimental_control_v2\ad5764_io\coil_vref\coil_vref_terminal_v6.py --non-interactive', ts_channel=16)

vco_controller = VCOController(r'python  Q:\indium\software\experimental_control_v2\sweep_dds\vco_terminal_v7.py --non-interactive', ts_channel=13)


rf_knife_board = VCOController(r'python  Q:\indium\software\experimental_control_v2\rf_knife\vco_terminal_v7.py --non-interactive', ts_channel=44)
rf_knife_freq = rf_knife_board()
rf_knife_switch = TSChannel(channel=43, init_state=0, name='rf_knife_switch')

remote_sim_control = to_in_helm.conn.modules.lab_control.device.fname_gen.EMCCD_simControl

remote_config = to_in_helm.conn.modules.lab_control.core.config.config 
remote_config.output_dir = rf'd:\{datetime.now():%y%m%d}'
print(f'[INFO] Output directory is {remote_config.output_dir}. ')
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

# valon_synth = ValonSynthesizer(channel=38, freq=1000)
