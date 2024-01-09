import numpy as np 
from glob import glob 
from os.path import join 

def get_tif_fp(fname_prefix, parent_folder):
    """ 
    Note
    ---
    The length of fname_prefix is limited to 20 characters

    Example
    --- 
    ::

        fname = config.gen_fname_from_dict(config_dict)
        fp = get_tif_fp(fname, config.output_dir)
        
    """
    return open(glob(join(parent_folder, f'{fname_prefix[:20]}*.tif'))[0], 'rb') 

def get_tif_latest_single_image(fp): 
    """ Returns single image in NumPy array 
    """
    return np.frombuffer(fp.read()[-2*1024*1024:], np.uint16).astype(float).reshape(1024, 1024)

def get_roi_count(arr, roi):
    return arr[..., roi[0], roi[1]].sum(axis=-1).sum(axis=-1)
