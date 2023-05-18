from ..device import *
from ..remote.remote import to_sr_remote

# wlm_lock = to_sr_remote(WaveLengthMeterLock)(
#     r'"C:\Users\strontium_remote1\AppData\Local\Programs\Python\Python39\python" "C:\Users\strontium_remote1\Desktop\Lock-to-Wave-Meter\ui_multi.py"',
#     name_mapping=['679'],
#     ch_mapping={3:0})

oven_c = to_sr_remote(OvenController)(
    r'"C:\Users\strontium_remote1\AppData\Local\Programs\Python\Python39\python" "Q:\strontium\hardware\vacuum_chamber\source_and_viewport_temp_control\oven_control\terminal_software_v3.0.py" > oven_log.txt',
    )