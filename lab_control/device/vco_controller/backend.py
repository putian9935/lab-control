""" Compatible with lab control """
import os
import time
import sys
import aioserial
import numpy as np
from ast import literal_eval
import struct

def arduino_transaction(ser):
    """ make arduino calls multi-process safe """
    def ret(f):
        async def _inner(*args, **kwargs):
            ser.open()
            r = await f(*args, **kwargs)
            ser.close()
            return r
        return _inner
    return ret


def readback():
    """ while there is a receive, there is a print """
    while not ser.in_waiting:
        time.sleep(.02)
    while ser.in_waiting:
        print(ser.readline())

if __name__ == '__main__':
    com_port = 'COM23'
    # com_port = 'COM10' # on desktop 2
    ser = serial.AioSerial(baudrate=2000000, timeout=0.05)
    ser.port = com_port
    ser.dtr = False
    time.sleep(1)
    send_trig_disable()

@arduino_transaction(ser)
async def send_trig_disable():
    ser.write(bytes('TDS'+'\n', encoding='ascii'))


# interpolatation of relation bewteen DAC and detuning
Mhz = 1e6


def detuning2DDS(detuning):
    """ Convert detuning to DDS frequency tuning word
    
    Input
    --- 
    - detuning: the detuning from resonance. Red detuning takes **minus** sign. So MOT detuning 
    takes negative numbers now. 

    Note
    ---
    The conversion formula is: offset freq. = (detuning-823) / 16 

    The 651nm reference is locked at 651.403550nm. 
    """
    offset_freq = -(np.array(detuning) - 823) / 16 
    return (offset_freq / 250 * 2 ** 31).astype(np.uint32)



# @arduino_transaction(ser)
async def set_param(dt: list, v: list):
    ser.write(bytes('TDS'+'\n', encoding='ascii'))
    seq_len = len(dt)
    # send sequence length
    ser.write(bytes('SETL '+str(seq_len)+'\n', encoding='ascii'))
    readback()
    time.sleep(0.01)

    setdt_com = 'SETTA '+' '.join(map(str, dt))+'\n'
    ser.write(setdt_com.encode())
    readback()
    time.sleep(0.01)

    setv_com = 'SETDAC '+' '.join(map(str, v)) + '\n'
    ser.write(setv_com.encode())
    readback()
    time.sleep(0.01)

    
def ensure_vector(arr):
    ''' ensure arr is at least rank 1 '''
    if not arr.shape:
        return arr.reshape(-1)
    return arr


def set_paramDet_action(args):
    #     f = open(args.fname)
    #     print(f.readlines())
    contents = np.loadtxt(args.fname, delimiter=',', unpack=True)
    if not contents.size: return 
    dt, dv = contents
    dt = ensure_vector(dt)
    dv = ensure_vector(dv)
    dt = dt.astype(np.uint32)
    dv = detuning2DDS(dv)
    arrayToSend = tuple(map(tuple, [dt, dv]))
    print(arrayToSend)
    set_param(*arrayToSend)


# @arduino_transaction(ser)
async def exp_action():
    await ser.write_async(bytes('TEN'+'\n', encoding='ascii'))

# @arduino_transaction(ser)
async def stop():
    await ser.write_async(bytes('TDS'+'\n', encoding='ascii'))
