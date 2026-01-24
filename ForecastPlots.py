import numpy as np
from netCDF4 import Dataset
import datetime as dt
from collections import OrderedDict
import pandas as pd
import gc
import os

import matplotlib.pyplot as plt
from matplotlib import cm



def datefix(date):
        return date % 364

def makerange(y,x):
    numbers=[]
    if x < y:
        for n in range(y,365,1):
            numbers.append(n)
        for m in range(0,x,1):
            numbers.append(m)
        return numbers
    else:
        for n in range(y,x+1,1):
            numbers.append(n)
        return numbers

def getheight(past_array,fcst_array, per95_range,index,lat,lon):
    p_max = np.nanmax(past_array)
    f_max = np.nanmax(fcst_array[:,:,lat,lon])
    g_max = np.nanmax(per95_range)
    if p_max  > f_max:
        hdwmax = p_max
    else:
        hdwmax = f_max
    if hdwmax > g_max:
        height = hdwmax + 50
    else:
        height = g_max + 50
    return height

def get_current_day():
    # automaticaly pulls in today's date and removes 1 (zero-based)
    current_day = dt.date.today().timetuple().tm_yday  - 1

    # fix for leap years
    if int(dt.date.today().strftime('%Y')) % 4 ==0:
        if int(dt.date.today().strftime('%m')) > 2:
            current_day -= 1

    return current_day


def climo_background(ax, x, height, climo, Range, lat, lon):
    ''' ax is plot axis object
        x is either a list of datetime objects or '''
    alpha = 0.6
    #Range = np.arange(x[0].timetuple().tm_yday-1, x[-1].timetuple().tm_yday, 1)
    ax.fill_between(x,height,climo[4,Range,lat,lon],color = cm.YlOrBr(0.99),alpha = alpha, label = "Above 95th Percentile")
    ax.fill_between(x,climo[4,Range,lat,lon],climo[3,Range,lat,lon],color = cm.YlOrBr(0.80),alpha = alpha,\
                 label = "Above 90th Percentile")
    ax.fill_between(x,climo[3,Range,lat,lon],climo[2,Range,lat,lon],color = cm.YlOrBr(0.60),alpha = alpha,\
                 label = "Above 75th Percentile")
    ax.fill_between(x,climo[2,Range,lat,lon],climo[1,Range,lat,lon],color = cm.YlOrBr(0.40),alpha = alpha,\
                 label = "Above 50th Percentile")
    ax.fill_between(x,climo[1,Range,lat,lon],climo[0,Range,lat,lon],color = cm.YlOrBr(.20),alpha = alpha,\
                 label = "Above 25th Percentile")

def fcst_plot(fig,lat, lon, HDWpast, HDWfcst, climo, current_day, latvar, lonvar):
    ''' HDWpast should just be a 1D array length 10. '''
    ax = plt.gca()
    # create range of days for indicies
    Range = makerange(datefix(current_day - 11), datefix(current_day+7))

    # index for archive data
    index_arc = makerange(datefix(current_day-10),datefix(current_day-1))

    # Create the height of the plot
    height = getheight(HDWpast,HDWfcst,climo[4,Range,lat,lon],index_arc,lat,lon)

    #   CLIMO PERCENTILES
    # lines
    alpha = 0.5
    lw = 1
    x = range(0,19,1)
    colors = ['#46804e','#82ba09','#f9b106','#db3609','#7a1c09']
    colors = [cm.YlOrBr(0.40),cm.YlOrBr(0.50),cm.YlOrBr(0.70),cm.YlOrBr(0.85),cm.YlOrBr(0.99)]
    for perc in range(0,5,1):
        ax.plot(x, climo[perc,Range,lat,lon], color = colors[perc],alpha = alpha, linewidth = lw)

    # background fill
    climo_background(ax, x, height, climo, Range, lat, lon)

    # current day location
    ax.axvline(11, color = '#b50909', linewidth = 1, linestyle='--')

    #   ARCHIVE
    ax.plot(range(1,11,1), HDWpast[:], color = 'k', linewidth = 3, marker = 'o', label = 'GEFS 10-Day Analysis')

    #   FORECAST
    ms = 5 # markersize
    width = 1 #linewidth
    style = '-' #linestyle
    color =  '#525252'
    color2 = 'C0'

    # all members
    for member in range(1,20,1):
        # connector
        ax.plot([10,11], [HDWpast[-1],HDWfcst[0,member,lat,lon]], color = color,\
        linewidth = width, linestyle = style)
        # forecast
        ax.plot(range(11,18,1),HDWfcst[:,member,lat,lon], linewidth = width,linestyle = style, marker = 'o',\
         mec = 'k',markersize = ms, color = color, markerfacecolor = color2, label = 'GEFS Members')
    # control
    ax.plot([10,11], [HDWpast[-1],HDWfcst[0,0,lat,lon]], color = 'r',\
    linewidth = width+1, linestyle = style) ##0797f7
    # forecast
    ax.plot(range(11,18,1),HDWfcst[:,0,lat,lon], linewidth = width+1 ,linestyle = style, marker = 'o',\
     mec = 'k',markersize = ms, color ='r', label = 'GEFS Control')


    # fix end point of archive so forecast doesn't overlap
    index = makerange(datefix(current_day-2),datefix(current_day-1))
    ax.plot([9,10],HDWpast[-2:], marker = 'o',color = 'k')

    #   PLOT DETAILS

    # size of ticks and axis labels
    plt.xticks(fontsize = 20);
    plt.yticks(fontsize = 18);
    plt.ylabel("HDWI", fontsize = 24,labelpad=15, weight='bold')
    plt.xlabel("Day", fontsize = 24,labelpad=15, weight='bold')

    # title
    plt.figtext(.5, .99,'Max Daily HDWI',fontsize=28,ha='center', weight='bold')
    plt.figtext(.5, .945,'GEFS Analysis and Forecast & 1981-2010 CFSR Climatology',fontsize=22,ha='center')
    plt.figtext(.5,.90,str(latvar[lat])+r'$^{\circ}$N, '+str(abs(lonvar[lon]))+r'$^{\circ}$W',
            fontsize=22,ha='center', color='#21414c', weight='bold')

    # Make legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    Legend = ax.legend(by_label.values(), by_label.keys(),fontsize = 12, loc = 'upper left');
    # keep the background white
    Legend.get_frame().set_alpha(1)
    Legend.get_frame().set_edgecolor('k')

    # Modify x-axis
    date = dt.date.today().strftime('%m/%d')

    # Re-label x-axis
    xtick_locs= [0,1,3,5,7,9,11,13,15,17]
    xtick_lbls = ['',-10,-8,-6,-4,-2,date,'+2','+4','+6']
    plt.xticks(xtick_locs, xtick_lbls,);
    # Color xticks
    for count,xtick in enumerate(ax.get_xticklabels()):
        if count >= 6:
            xtick.set_color('#b50909')
        if count == 6:
            xtick.set_weight('bold')

    # set limits on axes
    ax.set_xlim(0,18);
    ax.set_ylim(0,height);



def plot_CONUS(lat_start, lat_end):

    # Forecast Data
    #directory_forecast = r'GEFS_fcst_dates/'
    #directory_forecast = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data/'
    directory_forecast = r'./'
    filename_forecast = r'GEFS_HDW_FCST.nc'

    # Past 10 Days Data
    #directory_past = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data/'
    directory_past = r'./'

    # Climate Data for Climatology
    #directory_climo = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_climo/'
    directory_climo = r'./'
    filename_climo = r'CFSR_MaxDHDW_CLIMO.nc'

    # Location where figures will be saved
    #directory_fig = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_GEFSplots/'
    directory_fig = r'./'

    ######
    ###### Everyhing below is what should be copied into new scripts
    ######
    ######

    # read in the land mask
    landpts = pd.read_csv('CONUS_land_indices.txt')
    lpts = list(zip(landpts['x'].values, landpts['y'].values))

    # automaticaly pulls in today's date and removes 1 (zero-based)
    current_day = get_current_day()

    # CLIMATOLOGY
    ncfile = Dataset('%s%s' % (directory_climo,filename_climo), 'r')
    # read in variables
    climo = ncfile.variables['climoARRAY'][:]
    latvar = ncfile.variables['latitude'][:]
    lonvar = ncfile.variables['longitude'][:]
    # close file
    ncfile.close()

    # FORECAST DATA
    ncfile_forecast = Dataset('%s%s' % (directory_forecast,filename_forecast), 'r')
    HDWfcst = ncfile_forecast.variables['HDWI'][:] #days, mem, lat, lon
    ncfile_forecast.close()

    # ANALYSIS DATA - for when we update to days in the filename
#     HDWpast = []
#     today = dt.date.today()
#     for t in np.arange(today-dt.timedelta(hours=24*10), today):
#         t = t.astype(dt.datetime)
#         filename = r'GEFS_HDW_ANL_day-{}.nc'.format(t.strftime('%Y%m%d'))
#         if os.path.exists('%s%s' % (directory_past,filename)):
#             ncfile = Dataset('%s%s' % (directory_past,filename), 'r')
#             HDWpast.append(ncfile.variables['HDWI'][:].data)#[lat,lon])
#             ncfile.close()

#         else:
#             HDWpast.append(np.full(shape=[len(latvar), len(lonvar)], fill_value=np.nan))
#     HDWpast = np.asarray(HDWpast)

    # ANALYSIS DATA - for now
    HDWpast = []
    for n in reversed(range(1,11,1)):
        filename = r'GEFS_HDW_ANL_day-'+str(n)+'.nc'
        # look for file. If it doesn't exist, append NaN to the analysis file
        try:
            ncfile = Dataset('%s%s' % (directory_past,filename), 'r')
            HDWpast.append(ncfile.variables['HDWI'][:].data)
            ncfile.close()
        except (OSError):
            HDWpast.append(np.full(shape=[len(latvar),len(lonvar)], fill_value=np.nan))
            pass
    HDWpast = np.asarray(HDWpast)

    # PLOTS
    for lat in range(lat_start, lat_end):
        for lon in range(0,len(lonvar)):
            # you are over land
            if (lat,lon) in lpts:

                fig = plt.figure(figsize=(15,10))
                fcst_plot(fig, lat, lon, HDWpast[:,lat,lon], HDWfcst, climo, current_day, latvar, lonvar)
                # save fig into whatever directory
                filename_fig = 'HDW_GEFS_'+str(latvar[lat])+'_'+str(lonvar[lon])+'.png'
                fig.savefig('%s%s' % (directory_fig,filename_fig),bbox_inches='tight');
                fig.clf()
                plt.close()
                gc.collect()


            
def plot_AK(lat_start, lat_end):

    # Forecast Data
    #directory_forecast = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data_AK/'
    directory_forecast = r'./'
    #directory_forecast = r'GEFS_fcst_AK/'
    filename_forecast = r'GEFS_HDW_FCST_AK.nc'

    # Past 10 Days Data
    #directory_past = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data_AK/'
    directory_past = r'./'
    #directory_past = r'GEFS_fcst_AK_dates/'

    # Climate Data for Climatology
    #directory_climo = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_climo_AK/'
    directory_climo = r'./'
    #directory_climo = r'climo_AK/'
    filename_climo = r'CFSR_MaxDHDW_CLIMO_AK.nc'

    # Location where figures will be saved
    #directory_fig = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_GEFSplots_AK/'
    directory_fig = r'./'
    #directory_fig = r'plots/'


    # automaticaly pulls in today's date and removes 1 (zero-based)
    current_day = get_current_day()

    # CLIMATOLOGY
    ncfile = Dataset('%s%s' % (directory_climo,filename_climo), 'r')
    # read in variables
    climo = ncfile.variables['climoARRAY'][:]
    latvar = ncfile.variables['latitude'][:]
    lonvar = ncfile.variables['longitude'][:]
    # close file
    ncfile.close()

    # FORECAST DATA
    ncfile_forecast = Dataset('%s%s' % (directory_forecast,filename_forecast), 'r')
    HDWfcst = ncfile_forecast.variables['HDWI'][:] #days, mem, lat, lon
    ncfile_forecast.close()

    # ANALYSIS DATA
    #HDWpast = []
    #today = dt.date.today()
    #for t in np.arange(today-dt.timedelta(hours=24*10), today):
    #    t = t.astype(dt.datetime)
    #    filename = r'GEFS_HDW_ANL_AK_day-{}.nc'.format(t.strftime('%Y%m%d'))
    #    if os.path.exists('%s%s' % (directory_past,filename)):
    #        ncfile = Dataset('%s%s' % (directory_past,filename), 'r')
    #        HDWpast.append(ncfile.variables['HDWI'][:].data)#[lat,lon])
    #        ncfile.close()

    #    else:
    #        HDWpast.append(np.full(shape=[len(latvar), len(lonvar)], fill_value=np.nan))
    #HDWpast = np.asarray(HDWpast)

    HDWpast = []
    for n in reversed(range(1,11,1)):
        filename = r'GEFS_HDW_ANL_AK_day-'+str(n)+'.nc'
        # look for file. If it doesn't exist, append NaN to the analysis file
        try:
            ncfile = Dataset('%s%s' % (directory_past,filename), 'r')
            HDWpast.append(ncfile.variables['HDWI'][:].data)
            ncfile.close()
        except (OSError):
            HDWpast.append(np.full(shape=[len(latvar),len(lonvar)], fill_value=np.nan))
            pass
    HDWpast = np.asarray(HDWpast)

    # PLOTS
    for lat in range(lat_start, lat_end):
        for lon in range(0,len(lonvar)):

            fig = plt.figure(figsize=(15,10))
            fcst_plot(fig, lat, lon, HDWpast[:,lat,lon], HDWfcst, climo, current_day, latvar, lonvar)
            # save fig into whatever directory
            filename_fig = 'HDW_GEFS_'+str(latvar[lat])+'_'+str(lonvar[lon])+'.png'
            fig.savefig('%s%s' % (directory_fig,filename_fig),bbox_inches='tight');
            fig.clf()
            plt.close()
            gc.collect()