#!/usr/bin/env python3

import numpy as np
from netCDF4 import Dataset
import datetime as dt

# Climate Data for Climatology
#directory_climo = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_climo/'
directory_climo = r'./'
filename_climo = r'CFSR_MaxDHDW_CLIMO.nc'

# Forecast Data
#directory_forecast = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data/'
directory_forecast = r'./'
filename_forecast = r'GEFS_HDW_FCST.nc'

# Location where figures will be saved
#directory_save = r'/home/jay/hdwi_2024_GFS_singleday/autoops/HDW_data/'
directory_save = r'./'
filename_ncfile = r'MaxHDWPercGrid.nc'

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
HDWfcst = ncfile_forecast.variables['HDWI'][0,:,:,:] #first day, mem, lat, lon
ncfile_forecast.close()

def get_current_day():
    # automaticaly pulls in today's date and removes 1 (zero-based)
    current_day = dt.date.today().timetuple().tm_yday  - 1

    # fix for leap years
    if int(dt.date.today().strftime('%Y')) % 4 ==0:
        if int(dt.date.today().strftime('%m')) > 2:
            current_day -= 1
    return current_day

current_day = get_current_day()

grid = np.zeros([len(latvar),len(lonvar)])
# fill grid based on highest percentile that max current day forecast exceeds
for lat in range(0,len(latvar)):
    for lon in range(0,len(lonvar)):
        maxval = max(HDWfcst[:,lat,lon])
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
                grid[lat,lon]  = 95
        else:
            grid[lat,lon] = 'NaN'

# make netCDF file
f = Dataset('%s%s' % (directory_save, filename_ncfile),'w', format='NETCDF4')

# create a description
f.description = "Array of form ['lats','lons'].\
                    The largest forecast HDW value (from all GEFS members' forecasts) for each grid point is given a value of 25, 50, 75, 90, or 95 based on the largest percentile it equals or exceeds. For example, a value of 50 means the HDW value fell between the 50th and 74th percentiles. A value of 0 means the HDW value fell between the 0th and 24th percentiles. A value of 95 is greater than or equal to the 95th percentile."
# create dimensions
f.createDimension('lons', len(lonvar))
f.createDimension('lats', len(latvar))

# create array
percARRAY = f.createVariable('PercentileGrid', 'f4',('lats','lons'))
latitude = f.createVariable('latitude','f4','lats')
longitude = f.createVariable('longitude','f4','lons')

# fill array
percARRAY[:,:] = grid
latitude[:] = latvar
longitude[:] = lonvar

# close 
f.close()