import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def hex_to_rgb(hex_string):
    '''
    Converts hex string to rgb colors
    
    Required input:
        hex_string (str) = String of characters representing a hex color.
                           May or ay not have a leading `#`
                           Any alpha value on the end will be stripped off
    Output:
        A list (length 3) of integers (range 0-255) of RGB values
    '''
    value = hex_string.strip("#")[:6] # removes hash symbol if present, alpha value on end
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_hex(tup3):
    '''
    Converts rgb 3-member list or array to hex colors
    
    Required input: 
        tup3 (tuple) = list (length 3) of RGB values in decimal 0-255 range   
        
    Output: 
        A String of 6 characters representing a hex color, with leading hash.
    '''
    return "#{:02x}{:02x}{:02x}".format(tup3[0],tup3[1],tup3[2])


def rgb_to_dec(rgb_list):
    '''
    Converts RGB (range 0-255) to decimal (range 0-1) colors (i.e. divides each value by 255)
    
    Required input:
        rgb_list (list): list (length 3) of RGB values (range 0-255)
        
    Output:
        A list (length 3) of decimal values (0-1)
    '''
    return [v/255 for v in rgb_list[:3]]


def dec_to_rgb(dec_list):
    '''
    Converts decimal (range 0-1) to RGB (range 0-255) colors
    
    Required input:
        dec_list (list): list (length 3) of decimal values (0-1)
        
    Output:
        A list (length 3) of RGB values (range 0-255)
    '''
    return [int(round(v*255)) for v in dec_list[:3]]


def get_continuous_cmap(hex_list, float_list=None, ncol=256):
    ''' 
    Creates and returns a color map that can be used in heat map figures.
        The parameter `float_list` can be used to control the spacing between colors:
            If float_list is not provided, color map graduates linearly between each color in hex_list.
            If float_list is provided, each color in hex_list is mapped to the respective relative location in float_list. 
        
    Required input:
        hex_list   (list): List of hex code strings
        
    Optional input:
        float_list (list): List of floats between 0 and 1, same length as hex_list. Must start with 0 and end with 1.
        ncol        (int): Number of colors in the final colormap - default is 256
    
    Output:
        A color map in matplotlib `LinearSegmentedColormap` object 
        '''
    
    rgb_list = [rgb_to_dec(hex_to_rgb(i)) for i in hex_list]
    if float_list:
        pass
    else:
        float_list = list(np.linspace(0,1,len(rgb_list)))
        
    cdict = dict()
    for num, col in enumerate(['red', 'green', 'blue']):
        col_list = [[float_list[i], rgb_list[i][num], rgb_list[i][num]] for i in range(len(float_list))]
        cdict[col] = col_list
    cmp = mcolors.LinearSegmentedColormap('my_cmp', segmentdata=cdict, N=ncol)
    return cmp



def grad_brite(xrgb,pcol=None,lite_0=0.0,lite_1=1.0,mid_lite=None,mid_spot=None, ncol=256):
    '''
    Remaps the color sequence xrgb (required) into a constant gradient of brightness 
        on the greyscale in 1 or 2 linear segments.
    Result is a color scale to use as a cmap in plotting.
    
    Required input: 
        xrgb     (list) = a list of rgb hex strings (form: 'Xrrggbb') giving sequence of colors;
                          it is assumed the first color at a position of 0.0 and the last at 1.0 for 
                          the interpolations described below.
    
    Optional arguments:
        pcol      (list) = a list of float positions on a scale 0.0-1.0 corresponding to colors in xrgb;
                           must be same length as xrgb (default is equally spaced)
                
        lite_0   (float) = brightness on scale 0.0-1.0 for first color in list (default 0.0)
        
        lite_1   (float) = brightness on scale 0.0-1.0 for last color in list (default 1.0)
        
        mid_lite (float) = if present, defines an intermediate point between 0.0 and 1.0 where
                           a third brightness level is defined. Two linear gradients of brightness 
                           are determined - one from 0.0 to mid_lite and one from mid_lite to 1.0.
                           Otherwise, a single linear gradient from positions 0.0 to 1.0 is defined.
        
        mid_spot (float) = position between 0.0 and 1.0 where mid_lite is placed;
                           ignored if mid_lite=None
                
        ncol       (int) = number of colors in the final colormap (default is 256)
        
    The returned result is a ncol-stepped colormap to use as a cmap in plotting
    '''

    luma = [0.30, 0.59, 0.11]      # NTSC luma perception weightings for R, G, B
        
    # Nip potential problems with inputs
    lite_0 = np.max([0.0,np.min([1.0,lite_0])]) # Range is 0-1
    lite_1 = np.min([1.0,np.max([0.0,lite_1])]) # Range is 0-1
    ncol   = np.max([2,np.min([1024,ncol])])    # Range is 2-1024
    
    # Produce a preliminary color map, size ncol, from input colors - brightness will be adjusted below
    if pcol:
        if pcol[0] != 0.0:
            sys.exit("ERROR - First color position must be 0.0.")
        if pcol[-1] != 1.0:
            sys.exit("ERROR - Last color position must be 1.0.")
        if len(xrgb) != len(pcol):
            sys.exit("ERROR - List of positions is not the same length as list of colors.")
        else:
            rez = get_continuous_cmap(xrgb, float_list=pcol, ncol=ncol) # Produce color gradient - linear interp'd
    else:
        rez = get_continuous_cmap(xrgb, ncol=ncol) # Produce color gradient - default to equally spaced

    # Find the brightnesses of the originally supplied/requested colormap
    lite_rez = [np.dot(luma,rez(i)[:3]) for i in range(rez.N)]
        
    # Map out the target brightesses for the color map based on inputs
    if mid_lite:         # Two linear segments to interpolate
        if mid_spot:
            mid_x = int(np.rint(mid_spot*(ncol-1)))
            mid_x = np.max([np.min([mid_x,(ncol-2)]),1]) # Ensures midpoint is not same as first or last point
            lite = [lite_0 + (mid_lite-lite_0)*i/mid_x for i in range(mid_x)] + [mid_lite + (lite_1-mid_lite)*i/(ncol-mid_x-1) for i in range(ncol-mid_x)]
        else:
            sys.exit("ERROR - Location for intermediate brightness unspecified.")
    else:                # Only one segment
        lite = [lite_0 + (lite_1-lite_0)*i/(ncol-1) for i in range(ncol)] 

    # Rescaling of brightnesses at each point to produce perceptually uniform gradients
    fact = np.array(lite)/np.array(lite_rez)    
    fact3 = np.repeat(fact, repeats=3).reshape(ncol,3)   # Expand out to 3 array elements for array multiplication
    nurez3 = np.multiply(fact3,rez(range(ncol))[:,:3])   # Scaled values into a numpy array
    nurez3 = np.where(nurez3>1.0,1.0,np.where(nurez3<0.0,0.0,nurez3))
    nurez4 = np.ones((ncol,4)) ; nurez4[:,:-1] = nurez3  # Tack the alphas back on (all set to opaque)
    
    # Create a matplotlib colormap list for output
    cmp = mcolors.ListedColormap(nurez4)
    
    return cmp

