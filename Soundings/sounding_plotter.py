from math import isclose

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

import metpy.calc as mpcalc
import metpy.constants as c
from metpy.plots import add_metpy_logo, add_timestamp, SkewT
from metpy.units import units

from datetime import datetime

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


def plot_skewt(df,plot_stability=True,plot_cin_cape=True,plot_indices=True,output_pdf=False,output_display=True):
    """
    Plots annotated Skew-T log-P diagram using metpy module, given a meteorological profile
    
    Required inputs:
        df (Pandas dataframe) = sounding data, containing columns for:
                                'pressure' [hPa], 'temperature' [˚C], 'dewpoint' [˚C],
                                wind 'speed' [kts] and 'direction' [˚]
    Optional inputs:         Default:
        plot_stability (bool) [True]  = Include/exclude shading that shows stability in each interval of profile
        plot_cin_cape  (bool) [True]  = Include/exclude shading that shows CIN and CAPE
        plot_indices   (bool) [True]  = Include/exclude values for key indices estimated from profile
        output_pdf     (bool) [False] = Produce a PDF file of the plot in current directory
        output_display (bool) [True]  = Generate a plot interactively on the screen
        
    Outputs:
        skew         (object)         = The generated plot as an object
    """
    ###############################################################
    ### Set up interctive display
    plt.close()
    if output_display:
        plt.ion()
    else:
        plt.ioff()
    
    ###############################################################
    ### Parse meteorological variables

    # We will pull the data out of the sounding data into individual variables and assign units.
    p = df['pressure'].values * units.hPa
    T = df['temperature'].values * units.degC
    Td = df['dewpoint'].values * units.degC
    wind_speed = df['speed'].values * units.knots
    wind_dir = df['direction'].values * units.degrees
    u, v = mpcalc.wind_components(wind_speed, wind_dir)
    

    ###############################################################
    ### Initialize plot

    # Create a new figure. The dimensions here give a good aspect ratio.
    fig = plt.figure(figsize=(14, 10))
    skew = SkewT(fig,rect=(0.05,0.1,0.7,0.8),rotation=45) # `rotation` sets the slope of the isotherms
###    skew = SkewT(fig, rotation=45) # `rotation` sets the slope of the isotherms
    text_edge = 0.76

    ###############################################################
    ### Block for calculating and plotting stability
    
    if plot_stability:
        
        # For showing stability categories - color choices
        c_stab = ["indigo","silver","cadetblue","turquoise","yellowgreen","gold","deeppink"]

        # Other profile quantities needed to estimate stability in each interval
        abs_tol = 0.2    # The ± temperature range for defining isothermal, adiabatic profile intervals
        t_inv = T[:len(p)-1] - T[1:]  # Negative is inversion
        t_dry = [np.nan] * (len(p)-1) # Negative is dry stable, positive unstable
        t_moi = [np.nan] * (len(p)-1) # Negative is stable
                                      #   positive while t_dry negative is conditionally unstable
                                      #   both positive is moist adiabatic

        for i in range(len(p)-1):     # Every interval between measurements in the sounding...
            t_dry[i] = mpcalc.dry_lapse(p[i+1],T[i],reference_pressure=p[i]) - T[i+1]
            t_moi[i] = mpcalc.moist_lapse(p[i+1:i+2],T[i],reference_pressure=p[i]) - T[i+1]

            t_type = [2] * (len(p)-1) # Codes for stability; default is generic "stable"

        # Here we use codes for profiles in each interval:
        #  0 = inversion
        #  1 = isothermal (±abs_tol)
        #  2 = stable
        #  3 = moist adiabatic (±abs_tol)
        #  4 = conditionally unstable
        #  5 = neutral or adiabatic (±abs_tol)
        #  6 = absolutely unstable
        for i in range(len(p)-1):     # Every interval between measurements in the sounding...
            if t_inv[i] <= 0:
                t_type[i] = 0         # inversion
            if t_dry[i] > 0:
                t_type[i] = 6         # unstable
            if t_moi[i].size == 1:
                if t_dry[i] < 0 and t_moi[i] > 0:
                    t_type[i] = 4     # conditionally unstable
                if isclose(t_moi[i].magnitude, 0, abs_tol=abs_tol):
                    t_type[i] = 3     # moist adiabatic
            if isclose(t_dry[i].magnitude, 0, abs_tol=abs_tol):
                t_type[i] = 5         # neutral or adiabatic
            if isclose(t_inv[i].magnitude, 0, abs_tol=abs_tol):
                t_type[i] = 1         # isothermal    

        for i in range(len(p)-1):     # Plot stability shading in each interval
            y = [p[i],p[i+1]]
            x1 = [T[i],T[i+1]]
            x2 = [(50.0 * units.degC),(50.0 * units.degC)]
            skew.shade_area(y, x1, x2, which='both', facecolor=c_stab[t_type[i]])

        plt.figtext(text_edge, 0.68,"Unstable", ha='left', va='center',fontsize=20,c=c_stab[6])
        plt.figtext(text_edge, 0.71,"Neutral or Adiabatic", ha='left', va='center',fontsize=20,c=c_stab[5])
        plt.figtext(text_edge, 0.74,"Conditionally Unstable", ha='left', va='center',fontsize=20,c=c_stab[4])
        plt.figtext(text_edge, 0.77,"Moist Adiabatic", ha='left', va='center',fontsize=20,c=c_stab[3])
        plt.figtext(text_edge, 0.80,"Stable", ha='left', va='center',fontsize=20,c=c_stab[2])
        plt.figtext(text_edge, 0.83,"Isothermal", ha='left', va='center',fontsize=20,c=c_stab[1])
        plt.figtext(text_edge, 0.86,"Inversion", ha='left', va='center',fontsize=20,c=c_stab[0])


    ###############################################################
    ### Standard sounding plot

    skew.ax.set_ylim(1050, 100) # set pressure level range
    skew.ax.set_xlim(-40, 50)   # set temperature range on bottom of plot
    skew.plot(p, T, 'crimson')
    skew.plot(p, Td, 'teal')
    p_top = np.where(p.magnitude>=100.0)[0][-1] # truncate at top of plot
    skew.plot_barbs(p[:p_top], u[:p_top], v[:p_top])
   
    # Calculate LCL height and plot as black dot
    lcl_pressure, lcl_temperature = mpcalc.lcl(p[0], T[0], Td[0])
    skew.plot(lcl_pressure, lcl_temperature, 'ko', markerfacecolor='black')
   
    # Place markers at surface values of T, Td
    skew.plot(p[0], T[0], color='maroon', marker='x')
    skew.plot(p[0], Td[0], color='darkslategrey', marker='x')

    # Calculate full lifted parcel profile and add to plot as black line
    prof = mpcalc.parcel_profile(p, T[0], Td[0]).to('degC')
    skew.plot(p, prof, 'k', linewidth=1)
    
    # Mark the LFC, EL
    t_parcel = mpcalc.parcel_profile(p, T[0], Td[0]) 
    lfc_pressure,lfc_temperature = mpcalc.lfc(p, T, Td, t_parcel)
    skew.plot(lfc_pressure, lfc_temperature, 'wo', markerfacecolor='red')
    el_pressure,el_temperature = mpcalc.el(p, T, Td, which='most_cape')
    skew.plot(el_pressure, el_temperature, 'wo', markerfacecolor='sienna')

    
    # An example of a slanted line at constant T -- in this case the 0
    # isotherm
    skew.ax.axvline(0, color='grey', linestyle='-.', linewidth=1)
    

    ###############################################################
    ### Shade areas of CAPE and CIN, plot stats   
    if plot_cin_cape:
        skew.shade_cin(p, T, t_parcel)
        skew.shade_cape(p, T, t_parcel)
    

    ###############################################################
    ### Plot stability indices, other statistics 
    if plot_indices:
        c_cape,c_cin = mpcalc.cape_cin(p, T, Td, t_parcel, which_lfc='bottom', which_el='top')
        c_lcl_p,c_lcl_t = mpcalc.lcl(p[0], T[0], Td[0], max_iters=50, eps=1e-05)
        c_lcl_z = ((T[0]-Td[0]) * (125 * units.m / units.degK)).to_base_units()
        c_el_p,c_el_t = mpcalc.el(p, T, Td, which='most_cape')
        c_pw = mpcalc.precipitable_water(p,Td)
        c_lfc_p,c_lfc_t = mpcalc.lfc(p, T, Td, t_parcel, which='top')

        if not np.isnan(c_el_p.magnitude):
            plt.figtext(text_edge, 0.47,"EL: "+('%.0f' % c_el_p.magnitude)+" hPa", ha='left', va='center',fontsize=20,c='sienna')
            plt.figtext(text_edge, 0.44,"EL: "+('%.1f' % c_el_t.magnitude)+"˚C", ha='left', va='center',fontsize=20,c='sienna')
        if not np.isnan(c_lfc_p.magnitude):
            plt.figtext(text_edge, 0.39,"LFC: "+('%.1f' % c_lfc_p.magnitude)+" hPa", ha='left', va='center',fontsize=20,c='tab:red')
            plt.figtext(text_edge, 0.36,"LFC: "+('%.1f' % c_lfc_t.magnitude)+"˚C", ha='left', va='center',fontsize=20,c='tab:red')
        plt.figtext(text_edge, 0.305,"CAPE: "+('%.0f' % c_cape.magnitude)+" J/kg", ha='left', va='center',fontsize=20,c='firebrick')
        plt.figtext(text_edge, 0.265,"CIN: "+('%.0f' % c_cin.magnitude)+" J/kg", ha='left', va='center',fontsize=20,c='blue')
        plt.figtext(text_edge, 0.21,"PW: "+('%.0f' % c_pw.magnitude)+" mm", ha='left', va='center',fontsize=20,c='lightseagreen')
        plt.figtext(text_edge, 0.16,"LCL: "+('%.0f' % c_lcl_p.magnitude)+" hPa", ha='left', va='center',fontsize=20,c='black')
        plt.figtext(text_edge, 0.13,"LCL: "+('%.1f' % c_lcl_t.magnitude)+"˚C", ha='left', va='center',fontsize=20,c='black')
       

    ###############################################################
    ### Plot the relevant thermodynamic lines
    skew.plot_dry_adiabats(alpha=0.25, color='orangered')
    skew.plot_moist_adiabats(alpha=0.25, color='tab:green')
    skew.plot_mixing_lines(pressure=np.arange(1050, 80, -20) * units.hPa,linestyle='dotted', color='tab:blue',
            mixing_ratio=np.array([2.5e-6,1e-5,3e-5,8e-5,2e-4,5e-4,0.001,0.002,0.004,0.007,0.01,0.016,0.024,0.032]).reshape(-1, 1))

    plt.tick_params(axis = 'y', which = 'major', labelsize = 16)
    plt.tick_params(axis = 'x', which = 'major', labelsize = 16, labelrotation=45)

    # Add the timestamp for the data to the plot
    s_site = df['station'][0]
    s_time = '{dt:%Y%m%d_%H%M}'.format(dt=df['time'][0])
    add_timestamp(skew.ax, datetime.strptime(s_time, '%Y%m%d_%H%M'), pretext='Valid: ', y=1.02, x=-0.1, ha='left', fontsize=17)
    skew.ax.set_title(s_site,fontsize=28)


    ###############################################################
    ### Produce a PDF file of the plot
    if output_pdf:
        filename = s_site+"_"+s_time+".pdf"
        plt.savefig(filename)
    
    return skew
