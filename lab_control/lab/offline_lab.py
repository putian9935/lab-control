from lab_control.device import *
import numpy as np 

TSChannel  = TimeSequencer()

AIO0 = AIO(
    port='COM22',
    minpd=np.array([32953., 32757., 29991., 32786.]),
    maxpd=np.array([34337., 35066., 32848., 33277.]),
    ts_mapping={ramp: 7, hsp: 18})