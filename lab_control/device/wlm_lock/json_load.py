import json 
import os.path
from functools import partial 

print = partial(print, flush=True)
def fill_missing_attr(laser_arr):
    attrs = ['ArduinoPin', 'WaveMeterChannel', 'SetWaveLength', 'Kp', 'Ki', 'Kd']
    default_value = dict(zip(attrs, [-1, -1, -1, 0, 0, 0]))
    for laser in laser_arr:
        for attr in attrs:
            if attr not in laser:
                laser[attr] = default_value[attr]


def load_settings(fname=None):
    if fname is None:
        dirname = os.path.dirname(__file__) 
        parent = os.path.dirname(dirname)
        settings = json.load(open(os.path.join(parent, 'wlm.json')))
    else:
        settings = json.load(open(fname))
        
    lasers = settings['Lasers']
    fill_missing_attr(lasers)
    return lasers