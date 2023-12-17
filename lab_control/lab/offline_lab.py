from lab_control.device import *
import numpy as np 
from lab_control.core.config import config

config.output_dir = rf'.'
config.view=False
config.offline=False
TSChannel  = TimeSequencer()

# AIO0 = AIO(
#     r'python C:\Users\Administrator\Desktop\v1.0\terminal\terminal.py --non-interactive',
#     minpd=np.array([32953., 32757., 29991., 32786.]),
#     maxpd=np.array([34337., 35066., 32848., 33277.]),
#     ts_mapping={ramp: 7, hsp: 18},
#     name='aio0')

sw = TSChannel(channel =20, delay=1) 