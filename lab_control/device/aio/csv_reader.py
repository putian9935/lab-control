from typing import List 

def binarise(*args):
    if len(args) == 2:
        # ramp 
        x, y = args
        return int(x).to_bytes(4, 'little', signed=False)+int(y).to_bytes(2, 'little', signed=False)
    elif len(args) == 1:
        # hsp
        y, = args
        return int(1).to_bytes(4, 'little', signed=False)+int(y).to_bytes(2, 'little', signed=False)

def fname2tv(fname):
    with open(fname) as fin:
        # line comment start with #
        return zip(*(line.strip().split() for line in fin if len(line.strip()) and line.strip()[0] != '#'))

def tv2wfm(time, val):
    """ Translate time and voltage to bitstream. """
    bs = b''.join(binarise(*_) for _ in zip(time, val))
    return len(bs).to_bytes(4, 'little') + bs

def p2r(val: List[str], maxpd: float, minpd: float):
    """ Translate percentage to raw. """
    span = maxpd - minpd
    return (int(float(_)*span + minpd) for _ in val)

def tran_wfm(fname, maxpd, minpd):
    time, val = fname2tv(fname)
    return tv2wfm(time, p2r(val, maxpd, minpd))

def get_wfm(fname):    
    return tv2wfm(*fname2tv(fname))
