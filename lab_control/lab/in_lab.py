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
    maxpd=np.array([62600.,    19065.,     0.,     0.]),
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

valon_synth = ValonSynthesizer(device_name='ASRL16::INSTR', channel=38, freq=1000)

valon_synth_56 = ValonSynthesizer(device_name='ASRL9::INSTR', channel=45, freq=1753)
gm_switch = valon_synth_56(target=valon_synth_56, init_state=1)

from lab_control.core.util.unit import s, ms, us
emccd_trig = TSChannel(pulse, channel=10, delay=2*ms, name='emccd_trig')
cmos_trig = TSChannel(pulse, channel=24, delay=250, name='emccd_trig')

# All AOM and shutter on in init_state
mot_aom = TSChannel(channel=7, init_state=1, name='mot_aom')
aom_451_slave = TSChannel(channel=19, init_state=1, name='aom_451_slave')
aom_451_master = TSChannel(channel=37, init_state=1, name='aom_451_master')
aom_410_slave = TSChannel(channel=36, init_state=1, name='aom_410_slave') 
aom_410_master = TSChannel(channel=20, init_state=1, name='aom_410_master') 
odt = TSChannel(channel=21, init_state=1, name='odt')
aom_451_65 = TSChannel(channel=30, init_state=1, name='aom_451_65')
aom_451_34 = TSChannel(channel=33, init_state=0, name='aom_451_34')
aom_410_44 = TSChannel(channel=35, init_state=0, name='aom_410_44')
mw_switch = TSChannel(channel=38, init_state=0, name='mw_switch')

igbt0 = TSChannel(channel=1, init_state=0, name='igbt0')
igbt1n2 = TSChannel(channel=2, init_state=0, name='igbt1n2')
igbt3n4 = TSChannel(channel=3, init_state=1, name='igbt3n4')
field_unlock = TSChannel(channel=5, init_state=1, name='field_unlock')

zm_rp_shutter = TSChannel(channel=6, init_state=0, name='zm_rp_shutter')
zm_shutter = TSChannel(channel=8, init_state=1, name='zm_shutter')
mot_shutter = TSChannel(channel=11, init_state=0, name='mot_shutter')
mot_xy_shutter = TSChannel(channel=27, init_state=1, name='mot_xy_shutter')
mot_410_shutter = TSChannel(channel=26, init_state=0, name='mot_410_shutter')
mot_451_shutter = TSChannel(channel=29, init_state=0, name='mot_451_shutter')
mot_z_shutter = TSChannel(channel=34, init_state=0, name='mot_451_shutter')
stirap_410_shutter = TSChannel(channel=39, init_state=0, name='stirap_410_shutter')

osc_trig = TSChannel(channel=56, init_state=0, name='osc_trig')


