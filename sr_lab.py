from devices import * 

import numpy as np 
AIO0 = AIO(port='COM22', minpd=np.array([32953., 32757., 29991., 32786.]), maxpd=np.array([34337., 35066., 32848., 33277.]), ts_mapping={ramp:7, hsp:18}) 
AndorCamera = Camera(channel=2)
RawTS = TimeSequencer()
ts_sr = TimeSequencerFPGA('192.168.107.146', 5555)

fname_gen = FileNameGenerator()
