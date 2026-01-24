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

def get_current_day():
    # automaticaly pulls in today's date and removes 1 (zero-based)
    current_day = dt.date.today().timetuple().tm_yday  - 1

    # fix for leap years
    if int(dt.date.today().strftime('%Y')) % 4 ==0:
        if int(dt.date.today().strftime('%m')) > 2:
            current_day -= 1
            
    return current_day

def get_percentile_grid(current_day, latvar, lonvar, HDWfcst, climo):
    # create grid of zeroes
    grid = np.zeros([len(latvar),len(lonvar)])
    # fill grid based on highest percentile that max current day forecast exceeds
    for lat in range(0,len(latvar)):
        for lon in range(0,len(lonvar)):
            maxval = max(HDWfcst[0,:,lat,lon])
            if maxval != 'NaN':
                if maxval >= climo[0,current_day,lat,lon]:
                    grid[lat,lon]  = 25
                if maxval >= climo[1,current_day,lat,lon]:
                    grid[lat,lon]  = 50
                if maxval >= climo[2,current_day,lat,lon]:
                    grid[lat,lon]  = 75
                if maxval >= climo[3,current_day,lat,lon]:
                    grid[lat,lon]  = 90
                if maxval >= climo[4,current_day,lat,lon]:
                    grid[lat,lon]  = 96
            else:
                grid[lat,lon] = 'NaN'
    return grid

def get_median_percentile_grid(current_day, latvar, lonvar, HDWfcst, climo):
    # create grid of zeroes
    grid = np.zeros([len(latvar),len(lonvar)])
    # fill grid based on highest percentile that max current day forecast exceeds
    for lat in range(0,len(latvar)):
        for lon in range(0,len(lonvar)):
            medianval = np.median(HDWfcst[0,:,lat,lon])
            if medianval != 'NaN':
                if medianval >= climo[0,current_day,lat,lon]:
                    grid[lat,lon]  = 25
                if medianval >= climo[1,current_day,lat,lon]:
                    grid[lat,lon]  = 50
                if medianval >= climo[2,current_day,lat,lon]:
                    grid[lat,lon]  = 75
                if medianval >= climo[3,current_day,lat,lon]:
                    grid[lat,lon]  = 90
                if medianval >= climo[4,current_day,lat,lon]:
                    grid[lat,lon]  = 96
            else:
                grid[lat,lon] = 'NaN'
    return grid


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
# get plot info
perc_levels = [0,24,49,74,89,94,100]
perc_levels_cbar = [0,25,50,75,90,95,100]
perc_colors = ['w',cm.YlOrBr(0.20), cm.YlOrBr(0.40),cm.YlOrBr(0.60),cm.YlOrBr(.80),cm.YlOrBr(.99)]

def plot_CONUS():
    # Climate Data for Climatology
    #directory_climo = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_climo/'
    directory_climo = r'./'
    filename_climo = r'CFSR_MaxDHDW_CLIMO.nc'

    # Forecast Data
    #directory_forecast  = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data/'
    directory_forecast  = r'./'
    filename_forecast = r'GEFS_HDW_FCST.nc'

    # Location where figures will be saved
    #directory_fig = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_GEFSplots/'
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
    
    # find current day and make percentiles grid
    current_day = get_current_day()
    grid = get_percentile_grid(current_day, latvar, lonvar, HDWfcst, climo)
    grid_median = get_median_percentile_grid(current_day, latvar, lonvar, HDWfcst, climo)
    
    # Plotting Max Plot
    # PLOT
    fig = plt.figure(figsize=(15,12))
    ax = fig.add_subplot(111, projection=crs)
    ax.set_extent([lonvar[0],lonvar[-1], latvar[0], latvar[-1]], crs=ccrs.PlateCarree())
    ax.set_aspect('auto')

    x, y = np.meshgrid(lonvar,latvar)
    cs = ax.contourf(x,y,grid,levels = perc_levels,\
                  colors = perc_colors, alpha = 0.8, transform=ccrs.PlateCarree())

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
    plot_lat_lon(ax, meridians, parallels, top_label=True, left_label=True, bottom_label=False, right_label=True, linewidth=2.5,
                    color='gray', text_color='#444444',text_size=13,  linestyle=(0, (1, 3)))

    #NEW - Today's actual date
    todays_date = dt.date.today().strftime('%d %b %Y ')
    Title = plt.title(todays_date+'Max GEFS HDWI Forecast Percentiles',fontsize = 28, y =1.06, weight='bold')
    ax.text(0.015,0.02, 'Created '+dt.datetime.utcnow().strftime('%H%M UTC'),fontsize=16,
                        ha='left',va='bottom',color='#21414c',transform=ax.transAxes, zorder=32, 
           weight='bold') #,fontweight='bold'


    #colorbar
    ax1 = plt.gca()
    divider = make_axes_locatable(ax1)
    cax = divider.append_axes("bottom", size="2.5%", pad='3.5%', axes_class=plt.Axes) #2% sets thickness of colorbar
    cbar = plt.colorbar(cs, cax=cax, orientation='horizontal')
    #cbar.ax.set_aspect(.03) # sets width of colorbar
    cbar.ax.set_aspect(.025)
    cbar.set_label('Percentile Exceeded from 1981-2010 Climatology',fontsize=20, labelpad=8)
    cbar.ax.tick_params(labelsize=16)
    cbar.ax.set_xticklabels(perc_levels_cbar)

    # mostly fixes issues with plot outline being cut off
    #ax.outline_patch.set_visible(False)
    #for txt in ['left', 'right', 'bottom', 'top']:
    #    ax.spines[txt].set_visible(True) 
    #    ax.spines[txt].set_linewidth(1.5)
    #    ax.spines[txt].set_zorder(32)
     

    im = plt.imread('HDWLogo_Light.png')
    ax2 = fig.add_axes([0.795, 0.145, 0.1, 0.16], zorder=30)
    ax2.imshow(im)
    ax2.axis('off')


    #shows figure and saves it
    fig.savefig(f'{directory_fig}ConusPerc.png',bbox_inches='tight', dpi=150)
    plt.close(fig)
      
        
    ###############################################
    ###############################################
    # plotting Median Plot
     
    fig = plt.figure(figsize=(15,12))
    ax = fig.add_subplot(111, projection=crs)
    ax.set_extent([lonvar[0],lonvar[-1], latvar[0], latvar[-1]], crs=ccrs.PlateCarree())
    ax.set_aspect('auto')

    x, y = np.meshgrid(lonvar,latvar)
    cs = ax.contourf(x,y,grid_median,levels = perc_levels,\
                  colors = perc_colors, alpha = 0.8, transform=ccrs.PlateCarree())

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
    plot_lat_lon(ax, meridians, parallels, top_label=True, left_label=True, bottom_label=False, right_label=True, linewidth=2.5,
                    color='gray', text_color='#444444',text_size=13,  linestyle=(0, (1, 3)))

    #NEW - Today's actual date
    todays_date = dt.date.today().strftime('%d %b %Y ')
    Title = plt.title(todays_date+'Median GEFS HDWI Forecast Percentiles',fontsize = 28, y =1.06, weight='bold')
    ax.text(0.015,0.02, 'Created '+dt.datetime.utcnow().strftime('%H%M UTC'),fontsize=16,
                        ha='left',va='bottom',color='#21414c',transform=ax.transAxes, zorder=32, 
           weight='bold') #,fontweight='bold'


    #colorbar
    ax1 = plt.gca()
    divider = make_axes_locatable(ax1)
    cax = divider.append_axes("bottom", size="2.5%", pad='3.5%', axes_class=plt.Axes) #2% sets thickness of colorbar
    cbar = plt.colorbar(cs, cax=cax, orientation='horizontal')
    #cbar.ax.set_aspect(.03) # sets width of colorbar
    cbar.ax.set_aspect(.025)
    cbar.set_label('Percentile Exceeded from 1981-2010 Climatology',fontsize=20, labelpad=8)
    cbar.ax.tick_params(labelsize=16)
    cbar.ax.set_xticklabels(perc_levels_cbar)

    # mostly fixes issues with plot outline being cut off
    #ax.outline_patch.set_visible(False)
    #for txt in ['left', 'right', 'bottom', 'top']:
    #    ax.spines[txt].set_visible(True) 
    #    ax.spines[txt].set_linewidth(1.5)
    #    ax.spines[txt].set_zorder(32)
     

    im = plt.imread('HDWLogo_Light.png')
    ax2 = fig.add_axes([0.795, 0.145, 0.1, 0.16], zorder=30)
    ax2.imshow(im)
    ax2.axis('off')


    #shows figure and saves it
    fig.savefig(f'{directory_fig}ConusPercMedian.png',bbox_inches='tight', dpi=150)
    plt.close(fig)
    
def plot_AK():
    #directory_climo = r'climo_AK/'
    #directory_climo = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_climo_AK/'
    directory_climo = r'./'
    filename_climo = r'CFSR_MaxDHDW_CLIMO_AK.nc'

    # Forecast Data
    #directory_forecast = r'GEFS_fcst_AK/'
    #directory_forecast = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data_AK/'
    directory_forecast = r'./'
    filename_forecast = r'GEFS_HDW_FCST_AK.nc'

    # Location where figures will be saved
    #directory_fig = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_GEFSplots_AK/'
    directory_fig = r'./'
    #directory_fig = r'plots/'


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
    
    # find current_day and make percentiles grid
    current_day = get_current_day()
    grid = get_percentile_grid(current_day, latvar, lonvar, HDWfcst, climo)
    grid_median = get_median_percentile_grid(current_day, latvar, lonvar, HDWfcst, climo)
    
   
    ###### Plotting MAx PLOT
    # PLOT
    fig = plt.figure(figsize=(13,15))
    
    ax = fig.add_subplot(111, projection=crs)
    ax.set_extent([lonvar[0],lonvar[-1], latvar[0], latvar[-1]], crs=ccrs.PlateCarree())
    ax.set_aspect('auto')

    x, y = np.meshgrid(lonvar,latvar)
    cs = ax.contourf(x,y,grid,levels = perc_levels,\
                  colors = perc_colors, alpha = 0.8, transform=ccrs.PlateCarree())

    # add land and water features
    ax.add_feature(states_provinces, edgecolor='k', linewidth=.8, zorder=31)
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

    #NEW - Today's actual date
    todays_date = dt.date.today().strftime('%d %b %Y ')
    Title = plt.title(todays_date+'Max GEFS HDWI Forecast Percentiles',fontsize = 28, y =1.06, weight='bold')
    ax.text(0.015,0.0158, 'Created '+dt.datetime.utcnow().strftime('%H%M UTC'),fontsize=16,
                        ha='left',va='bottom',color='#21414c',transform=ax.transAxes, zorder=32,fontweight='bold')

    #colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="2.2%", pad='3%', axes_class=plt.Axes) #2% sets thickness of colorbar
    #ess of colorbar
    cbar = plt.colorbar(cs, cax=cax, orientation='horizontal')
    cbar.ax.set_aspect(.03) # sets width of colorbar
    cbar.set_label('Percentile Exceeded from 1981-2010 Climatology',fontsize=20, labelpad=8)
    cbar.ax.tick_params(labelsize=16)
    cbar.ax.set_xticklabels(perc_levels_cbar)

    # fixes issues with plot outline being cut off
    ax.outline_patch.set_visible(False)
    for txt in ['left', 'right', 'bottom', 'top']:
        ax.spines[txt].set_visible(True) 
        ax.spines[txt].set_linewidth(1.5)
        ax.spines[txt].set_zorder(32)

    #im = plt.imread('/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_scripts/HDWLogo_Light.png')
    im = plt.imread('HDWLogo_Light.png')
    ax2 = fig.add_axes([0.14, 0.75, 0.1, 0.16], zorder=30)
    ax2.imshow(im)
    ax2.axis('off')

    #shows figure and saves it
    fig.savefig(f'{directory_fig}AKPerc.png',bbox_inches='tight', dpi=150)
    plt.close(fig)
    
    ###############################################
    ###############################################
    ###### Plotting Median PLOT
    # PLOT
    fig = plt.figure(figsize=(13,15))
    
    ax = fig.add_subplot(111, projection=crs)
    ax.set_extent([lonvar[0],lonvar[-1], latvar[0], latvar[-1]], crs=ccrs.PlateCarree())
    ax.set_aspect('auto')

    x, y = np.meshgrid(lonvar,latvar)
    cs = ax.contourf(x,y,grid_median,levels = perc_levels,\
                  colors = perc_colors, alpha = 0.8, transform=ccrs.PlateCarree())

    # add land and water features
    ax.add_feature(states_provinces, edgecolor='k', linewidth=.8, zorder=31)
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

    #NEW - Today's actual date
    todays_date = dt.date.today().strftime('%d %b %Y ')
    Title = plt.title(todays_date+'Median GEFS HDWI Forecast Percentiles',fontsize = 28, y =1.06, weight='bold')
    ax.text(0.015,0.0158, 'Created '+dt.datetime.utcnow().strftime('%H%M UTC'),fontsize=16,
                        ha='left',va='bottom',color='#21414c',transform=ax.transAxes, zorder=32,fontweight='bold')

    #colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("bottom", size="2.2%", pad='3%', axes_class=plt.Axes) #2% sets thickness of colorbar
    #ess of colorbar
    cbar = plt.colorbar(cs, cax=cax, orientation='horizontal')
    cbar.ax.set_aspect(.03) # sets width of colorbar
    cbar.set_label('Percentile Exceeded from 1981-2010 Climatology',fontsize=20, labelpad=8)
    cbar.ax.tick_params(labelsize=16)
    cbar.ax.set_xticklabels(perc_levels_cbar)

    # fixes issues with plot outline being cut off
    ax.outline_patch.set_visible(False)
    for txt in ['left', 'right', 'bottom', 'top']:
        ax.spines[txt].set_visible(True) 
        ax.spines[txt].set_linewidth(1.5)
        ax.spines[txt].set_zorder(32)

    #im = plt.imread('/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_scripts/HDWLogo_Light.png')
    im = plt.imread('HDWLogo_Light.png')
    ax2 = fig.add_axes([0.14, 0.75, 0.1, 0.16], zorder=30)
    ax2.imshow(im)
    ax2.axis('off')

    #shows figure and saves it
    fig.savefig(f'{directory_fig}AKPercMedian.png',bbox_inches='tight', dpi=150)
    plt.close(fig)