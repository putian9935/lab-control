from ..device import *

# wlm_lock = WaveLengthMeterLock(
#     r'"C:\Users\strontium_remote1\AppData\Local\Programs\Python\Python39\python" "C:\Users\strontium_remote1\Desktop\Lock-to-Wave-Meter\ui_multi.py"',
#     name_mapping=['679'],
#     ch_mapping={3:0})

oven_c = OvenController(
    r'"C:\Users\strontium_remote1\AppData\Local\Programs\Python\Python39\python" "C:\Users\strontium_remote1\Desktop\Lock-to-Wave-Meter\ui_multi.py" > oven_log.txt',
    )