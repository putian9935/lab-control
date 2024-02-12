import numpy as np
from scipy.optimize import curve_fit
from scipy.ndimage import gaussian_filter

from numba import njit 
@njit(boundscheck=False, fastmath=True)
def twoD_Gaussian(x_tuple, amplitude, x0, y0, sigma_x2, sigma_y2, theta, offset):
    (x,y) = x_tuple
    a = (np.cos(theta)**2)/(2*sigma_x2) + (np.sin(theta)**2)/(2*sigma_y2)
    b = -(np.sin(2*theta))/(4*sigma_x2) + (np.sin(2*theta))/(4*sigma_y2)
    c = (np.sin(theta)**2)/(2*sigma_x2) + (np.cos(theta)**2)/(2*sigma_y2)
    return offset + amplitude*np.exp( - (a*((x-x0)**2) + 2*b*(x-x0)*(y-y0) + c*((y-y0)**2)))


def parse_single_img(img, full = 250, quiet=True):
    """ Find out gaussian parameter of a single image  
    
    Parameter
    --- 
    - img: a NumPy array of size 1024x1024
    - full: size of the cut 
    """
    try:
        img_gauss_filter = gaussian_filter(img,sigma = 0)
        maxpoint = np.where(img_gauss_filter == img_gauss_filter.max())
        centre1 = maxpoint[0][0]
        centre2 = maxpoint[1][0]

        img_cut = img[int(centre1-full/2):int(centre1+full/2), int(centre2-full/2):int(centre2+full/2)]
        img_gau_cut = img_gauss_filter[int(centre1-full/2):int(centre1+full/2), int(centre2-full/2):int(centre2+full/2)]
        if not quiet:
            print(centre1,centre2)
        ###fitting full range
        X = np.linspace(-full/2, full/2, full)
        Y = np.linspace(-full/2, full/2,full)
        X, Y = np.meshgrid(X,Y)
        p_ini = [(img_gau_cut.max()-img_gau_cut.min())*2,0,0,13**2,15**2,0,480]
        if not quiet:
            print(p_ini)
        params,cov = curve_fit(twoD_Gaussian, (X.ravel(), Y.ravel()), img_cut.ravel(), p0=p_ini,xtol=3e-3, gtol=3e-3)
    except ValueError:
        return np.array([np.nan]*7)
    if not quiet:
        print(params)
    return params 
