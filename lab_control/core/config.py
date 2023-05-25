from .types import *
from datetime import datetime 
import os 

time_stamp = None
arguments: Dict = None

dirname = rf'Q:\indium\data\2023\{datetime.now():%y%m%d}'
if not os.path.exists(dirname):
    print('Making directory', dirname)
    os.mkdir(dirname)

all_fnames = os.path.join(dirname, 'fnames.txt')
if not os.path.exists(all_fnames):
    open(all_fnames, 'w').close()

def append_fname(fname: str):
    with open(all_fnames, 'a') as f:
       f.write(fname+'\n')

def get_cnt():
    ret = 0
    with open(all_fnames) as f:
        while f.readline():
            ret += 1 
    print(ret)
    return ret 