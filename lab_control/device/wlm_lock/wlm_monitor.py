''' pure monitor function, not in control of running the lock program '''

from lab_control.core.target import Target
from ctypes import cdll
import ctypes
from lab_control.core.types import Dict


def getWaveLengthAt(ch):
    '''
    Sample call: 
    1. wl = getWaveLengthAt(8)()
    '''
    # Load functions from HighFinesse .dll file
    wm_dll = cdll.LoadLibrary("C:\Windows\System32\wlmData.dll")

    # Read wavelength
    wm_dll.GetWavelengthNum.restype = ctypes.c_double
    return lambda: wm_dll.GetWavelengthNum(ctypes.c_long(ch), ctypes.c_double(0))


def check_okay(target_wavelength: Dict[int, float]):
    """ check if all channels are locked 
    
    Parameter
    --- 
    - target wavelength in <channel id>:<target wavelength> format
    ::

    check_okay(target_wavelength = {1: 651.40401, 4: 651.40416})
    """
    wavelength_readers = [getWaveLengthAt(ch)
                          for ch in target_wavelength.keys()]

    def ret_func():
        ret = True
        for reader, (ch, target) in zip(wavelength_readers, target_wavelength.items()):
            x = reader()
            # the error is a bit rough, but should be fine
            if abs(x - target) > 5e-5:
                ret = False
                print(
                    f'Channel {ch} unlocked! Target wavelength is {target}, but reading from wavemeter is {x}')
        return ret
    return ret_func


class WaveLengthMeterLockMonitor(Target):
    ''' Lock monitor '''

    def __init__(self, check_func) -> None:
        super().__init__()
        if check_func is None:
            check_func = check_okay
        self.check_func = check_func

    def test_precondition(self):
        return self.check_func()

    def test_postcondition(self) -> bool:
        return self.check_func()

