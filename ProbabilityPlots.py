import numpy as np
from netCDF4 import Dataset
import datetime as dt

import cartopy.crs as ccrs 
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
from metpy.plots import USCOUNTIES

from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, to_rgba
import cmocean as cmo

#####
def get_current_day():
    # automaticaly pulls in today's date and removes 1 (zero-based)
    current_day = dt.date.today().timetuple().tm_yday  - 1

    # fix for leap years
    if int(dt.date.today().strftime('%Y')) % 4 ==0:
        if int(dt.date.today().strftime('%m')) > 2:
            current_day -= 1
            
    #print("current_day =",current_day)
    return current_day

def get_probs(day_len, prob_len, current_day, HDWfcst, climo, latvar, lonvar):
    # calculate probability
    probs = np.zeros([prob_len,day_len,len(latvar),len(lonvar)])
    for lat,_ in enumerate(latvar):
        for lon,_ in enumerate(lonvar):

            for day in range(0,day_len):
                for val in HDWfcst[day,:,lat,lon]:
                    if val != 'NaN':

                        #print(current_day," ",day)
                        if val >= climo[1,current_day+day,lat,lon]:
                            probs[0,day,lat,lon] += 1
                        if val >= climo[2,current_day+day,lat,lon]:
                            probs[1,day,lat,lon] += 1
                        if val >= climo[3,current_day+day,lat,lon]:
                            probs[2,day,lat,lon] += 1
                        if val >= climo[4,current_day+day,lat,lon]:
                            probs[3,day,lat,lon] += 1
    probs = probs/21   
    return probs

def plot_lat_lon(ax, lon_labels, lat_labels, top_label=False, left_label=False, bottom_label=True, right_label=True, linewidth=1,
                color='gray', text_color='gray',text_size=15, alpha=0.5, linestyle='--',zorder=100):

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=linewidth, color=color, alpha=alpha, linestyle=linestyle, zorder=zorder)
    gl.top_labels = True
    gl.left_labels = left_label
    gl.bottom_labels = bottom_label
    gl.right_labels = right_label
    #gl.xlines = False
    gl.xlocator = mticker.FixedLocator(lon_labels)
    gl.ylocator = mticker.FixedLocator(lat_labels)
    gl.xformatter = LONGITUDE_FORMATTER

    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': text_size, 'color': text_color}
    gl.ylabel_style = {'size': text_size, 'color': text_color}
    
# controls number of days and percentiles to calculate probs
day_len = 7
prob_len = 4 


# get cartopy info
crs = ccrs.PlateCarree()
water = "#abc0c7"#'#d7e9ef'

states_provinces = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lakes',
        scale='10m',
        facecolor='none')

lakes_50m = cfeature.NaturalEarthFeature('physical', 'lakes', '50m',
                                        edgecolor='face',
                                        facecolor=water)
rivers_50m = cfeature.NaturalEarthFeature('physical', 'rivers_lake_centerlines', '50m', facecolor='none',
                                         edgecolor='#86a5b0')
ocean_50m = cfeature.NaturalEarthFeature('physical', 'ocean', '50m',
                                        edgecolor='face',
                                        facecolor=water)

get_perc = {0:50, 1:75, 2:90, 3:95}

# Create Color Map
#color_list = [(cmo.cm.amp(i)) for i in np.arange(0, 1, .1)]
color_list = [(cmo.cm.amp(i)) for i in [0.,.075, .15, .225, .3, .38, .46, .58, .7, .85]]
color_list.insert(0, to_rgba('#ffffff'))
mycmap = LinearSegmentedColormap.from_list('c', color_list, N=58)
    
def plot_CONUS():
    # Climate Data for Climatology
    #directory_climo = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_climo/'
    directory_climo = r'./'
    filename_climo = r'CFSR_MaxDHDW_CLIMO.nc'

    # Forecast Data
    #directory_forecast = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data/'
    directory_forecast = r'./'
    filename_forecast = r'GEFS_HDW_FCST.nc'

    # Location where figures will be saved
    #directory_fig = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_GEFSprobs/'
    directory_fig = r'./'

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


    current_day = get_current_day()
    probs = get_probs(day_len, prob_len, current_day, HDWfcst, climo, latvar, lonvar)

    # Loop through days ( current,day1-day6 AND percentiles)
    for day in range(0,day_len):
        for prob in np.arange(0,prob_len): # 50, 75, 90, 95
            i,j = day, prob

            # get percentile for title and savefig
            perc = get_perc[prob]

            fig = plt.figure(figsize=(15,12))
            ax = fig.add_subplot(111, projection=crs)
            ax.set_extent([lonvar[0],lonvar[-1], latvar[0], latvar[-1]], crs=ccrs.PlateCarree())
            ax.set_aspect('auto')

            x, y = np.meshgrid(lonvar,latvar)
            grid = probs[prob,day,:,:]
            cs = ax.contourf(x, y, grid, cmap = mycmap,levels=np.arange(0,1.05,.1), alpha=0.99)
            cs.set_clim(0,.99)


            # add land and water features
            ax.add_feature(states_provinces, edgecolor='k', alpha=1, linewidth=.8, zorder=31)
            ax.add_feature(ocean_50m, zorder=30)
            ax.add_feature(rivers_50m)
            ax.add_feature(lakes_50m)
            ax.add_feature(USCOUNTIES.with_scale('20m'), linewidth=0.1,edgecolor='k')
            ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=31)
            ###############################################

            # NEW - add lat/lon lines
            meridians = np.arange(230., 310., 10.) - 360
            parallels = np.arange(20.,80,10.)
            plot_lat_lon(ax, meridians, parallels, top_label=True, left_label=True, bottom_label=False, right_label=True, linewidth=2.5, color='gray', text_color='#444444',text_size=13,  linestyle=(0, (1, 3)))


            #title
            now_day = dt.date.today() + dt.timedelta(hours=24*day)

            if day == 0:
                Title = plt.title(now_day.strftime('%d %b %Y')+\
                              ': Probability of HDWI Exceeding the '+str(perc)+'${\mathbf{^{th}}}$ Percentile',fontsize = 22
                          , y =1.07, weight='bold')
            else:
                Title = plt.title(now_day.strftime('%d %b %Y ')+'(Day +'+str(day)+\
                              '): Probability of HDWI Exceeding the '+str(perc)+'${\mathbf{^{th}}}$ Percentile',fontsize = 22
                          , y =1.07, weight='bold')


            #colorbar
            ax1 = plt.gca()
            divider = make_axes_locatable(ax1)
            cax = divider.append_axes("bottom", size="2.5%", pad='3.5%', axes_class=plt.Axes) #2% sets thickness of colorbar
            cbar = plt.colorbar(cs, cax=cax, orientation='horizontal')
            #cbar.ax.set_aspect(.03) # sets width of colorbar
            cbar.ax.set_aspect(.025)
            cbar.set_label('Probability from GEFS Members',fontsize=20, labelpad=8)
            cbar.ax.tick_params(labelsize=16)

            ## mostly fixes issues with plot outline being cut off
            #ax.outline_patch.set_visible(False)
            #for txt in ['left', 'right', 'bottom', 'top']:
            #    ax.spines[txt].set_visible(True) 
            #    ax.spines[txt].set_linewidth(1.5)
            #    ax.spines[txt].set_zorder(32)

            #shows figure and saves it
            fig.savefig(f'{directory_fig}Day{day}Perc{perc}.png',bbox_inches='tight', dpi=150)
            plt.close(fig)
            
def plot_AK():
    # Climate Data for Climatology
    #directory_climo = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_climo_AK/'
    directory_climo = r'./'
    #directory_climo = r'climo_AK/'
    filename_climo = r'CFSR_MaxDHDW_CLIMO_AK.nc'

    # Forecast Data
    #directory_forecast = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data_AK/'
    directory_forecast = r'./'
    #directory_forecast = r'GEFS_fcst_AK/'
    filename_forecast = r'GEFS_HDW_FCST_AK.nc'

    # Location where figures will be saved
    #directory_fig = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_GEFSprobs_AK/'
    directory_fig = r'./'

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


    current_day = get_current_day()
    probs = get_probs(day_len, prob_len, current_day, HDWfcst, climo, latvar, lonvar)

    # Loop through days ( current,day1-day6 AND percentiles)
    for day in range(0,day_len):
        for prob in np.arange(0,prob_len): # 50, 75, 90, 95
            i,j = day, prob

            # get percentile for title and savefig
            perc = get_perc[prob]

            fig = plt.figure(figsize=(13,15))
            ax = fig.add_subplot(111, projection=crs)
            ax.set_extent([lonvar[0],lonvar[-1], latvar[0], latvar[-1]], crs=ccrs.PlateCarree())
            ax.set_aspect('auto')

            x, y = np.meshgrid(lonvar,latvar)
            grid = probs[prob,day,:,:]
            cs = ax.contourf(x, y, grid, cmap = mycmap,levels=np.arange(0,1.05,.1), alpha=0.99)
            cs.set_clim(0,.99)


            # add land and water features
            ax.add_feature(states_provinces, edgecolor='k', alpha=1, linewidth=.8, zorder=31)
            ax.add_feature(ocean_50m, zorder=30)
            ax.add_feature(rivers_50m)
            ax.add_feature(lakes_50m)
            ax.add_feature(USCOUNTIES.with_scale('20m'), linewidth=0.1,edgecolor='k')
            ax.coastlines(resolution='50m', color='black', linewidth=1, zorder=31)
            ###############################################

            # NEW - add lat/lon lines
            meridians = np.arange(-170., -120., 10.) #- 360
            parallels = np.arange(50.,75.5,5.)
            plot_lat_lon(ax, meridians, parallels, top_label=True, left_label=True, bottom_label=False, right_label=True, linewidth=2.5,
                        color='gray', text_color='#444444',text_size=13,  linestyle=(0, (1, 3)))

            #title
            now_day = dt.date.today() + dt.timedelta(hours=24*day)

            if day == 0:
                Title = plt.title(now_day.strftime('%d %b %Y')+\
                              ': Probability of HDWI Exceeding the '+str(perc)+'${\mathbf{^{th}}}$ Percentile',fontsize = 22
                          , y =1.07, weight='bold')
            else:
                Title = plt.title(now_day.strftime('%d %b %Y ')+'(Day +'+str(day)+\
                              '): Probability of HDWI Exceeding the '+str(perc)+'${\mathbf{^{th}}}$ Percentile',fontsize = 22
                          , y =1.07, weight='bold')


            #colorbar
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("bottom", size="2.2%", pad='3%', axes_class=plt.Axes) #2% sets thickness of colorbar
            cbar = plt.colorbar(cs, cax=cax, orientation='horizontal')
            cbar.ax.set_aspect(.03) # sets width of colorbar
            cbar.set_label('Probability from GEFS Members',fontsize=20, labelpad=8)
            cbar.ax.tick_params(labelsize=16)

            #colorbar


            ## mostly fixes issues with plot outline being cut off
            #ax.outline_patch.set_visible(False)
            #for txt in ['left', 'right', 'bottom', 'top']:
            #    ax.spines[txt].set_visible(True) 
            #    ax.spines[txt].set_linewidth(1.5)
            #    ax.spines[txt].set_zorder(32)

            #shows figure and saves it
            fig.savefig(f'{directory_fig}Day{day}Perc{perc}_AK.png',bbox_inches='tight', dpi=150)
            plt.close(fig)