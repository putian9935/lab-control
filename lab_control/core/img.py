from PIL import Image 
from glob import glob 
import numpy as np 
from os.path import join 

def get_tif_handle(fname, parent_folder):
    """ return the TIFF handle with filename starts with `fname` and ends with '.tif' 

    Note 
    ---
    Only first match is returned 
    """
    return open(glob(join(parent_folder, f'{fname}*.tif'))[0], 'rb')
    
def get_single_tif_data(fp):
    """ returns single image """
    return np.frombuffer(fp.read()[-2*1024*1024:], dtype=np.uint16).astype(float).reshape(1024, 1024)