from lab_control.device import *
from ..remote.remote import to_sr_remote

import numpy as np

AIO0 = AIO(
    port='COM22',
    minpd=np.array([32953., 32757., 29991., 32786.]),
    maxpd=np.array([34337., 35066., 32848., 33277.]),
    ts_mapping={ramp: 7, hsp: 18})
# AndorCamera = Camera(channel=2)
# RawTS = TimeSequencer()
# ts_sr = TimeSequencerFPGA('192.168.107.146', 5555)
# fname_gen = FileNameGenerator()

# slm = SlaveLockMonitor(
#     r'"C:\Users\strontium_desktop2\miniconda3\python.exe" "C:\Users\strontium_desktop2\Desktop\putian\injection_stabilizer\script\gui.py"')

wlm_lock = to_sr_remote(WaveLengthMeterLock)(
    r'"C:\Users\strontium_remote1\AppData\Local\Programs\Python\Python39\python" "C:\Users\strontium_remote1\Desktop\Lock-to-Wave-Meter\ui_multi.py"')

# oven_c = to_sr_remote(OvenController)(
#     r'"C:\Users\strontium_remote1\AppData\Local\Programs\Python\Python39\python" "Q:\strontium\hardware\vacuum_chamber\source_and_viewport_temp_control\oven_control\terminal_software_v3.0.py" > oven_log.txt',
#     )
