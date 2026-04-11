import numpy as np
from netCDF4 import Dataset
import datetime as dt
from collections import OrderedDict
import pandas as pd
import gc
import os

import matplotlib.pyplot as plt
from matplotlib import cm

from flask import Flask, send_file, request
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)


def datefix(date):
        return date % 364

def makerange(y,x): #i just made this so i can wrap around dates
    numbers=[]
    if x < y: #if we need to wrap around the year
        for n in range(y,365,1):
            numbers.append(n) #list of numbers between y and 364
        for m in range(0,x,1): #list of numbers between 0 and x
            numbers.append(m)
        return numbers #combine both lists [y-364,0-x]
    else: #normal range
        for n in range(y,x+1,1): #simple range y to x
            numbers.append(n)
        return numbers


def get_current_day():
    return dt.date.today().timetuple().tm_yday - 1


def climo_background(ax,#plot axis object
                      x,#list of datetime objects or range of days
                    height, #how tall our plot is
                    climo, #array containing the precentiles for the lat/lon we're plotting
                    Range, #lookup table for x dates
                    lat, lon):

    alpha = 0.6 #a bit transparent

    ax.fill_between(x,#range of dates
                    height,#how tall
                    climo[4,Range,lat,lon], #95th percentile for our x dates, stored in range
                    color = "#420347",alpha = alpha)
    
    ax.fill_between(x,climo[4,Range,lat,lon],climo[3,Range,lat,lon],color = "#93099E",alpha = alpha)
    ax.fill_between(x,climo[3,Range,lat,lon],climo[2,Range,lat,lon],color = "#FF2B6F",alpha = alpha)
    ax.fill_between(x,climo[2,Range,lat,lon],climo[1,Range,lat,lon],color = "#FFB866",alpha = alpha)
    ax.fill_between(x,climo[1,Range,lat,lon],climo[0,Range,lat,lon],color = "#FBFC77",alpha = alpha)
    
def fcst_plot(fig, lat, lon, HDWpast, HDWfcst, climo, current_day, latvar, lonvar):
    ax = plt.gca()

    Range = makerange(datefix(current_day - 11), datefix(current_day + 7))  # entire range for when i add past


    fcst_vals = HDWfcst[:, :, lat, lon]   # gives me all forecast values for this lat/lon 
    height = 1.10 * np.nanmax(fcst_vals) #max height of plot


    n_fcst = HDWfcst.shape[0] #get number of forecast days
    fcst_x = np.arange(0, n_fcst) # x axis for forecast days
    x_all  = fcst_x # x axis including present (0) and forecast days

    # =========================

    present_idx_in_Range = 10  # when we ignore past values, today is in position 10
    Range_climo = Range[present_idx_in_Range : present_idx_in_Range + len(fcst_x)] # range of climo dates for present + forecast days

    climo_background(ax, x_all, height, climo, Range_climo, lat, lon)  #plot the climo background

 
    ms = 5
    width = 1
    style = '-'
    color = 'black'
    color2 = 'C0'

    ax.plot(0, HDWpast[-1], marker='o', color='k', markersize=5) #plot present point

    # =========================
    # ENSEMBLE MEMBERS
    # =========================
    for member in range(1, 20): #loop through ensemble members (gefs has 20))
        ax.plot(fcst_x,
                HDWfcst[:, member, lat, lon],
                linewidth=width, linestyle=style, marker='o',
                mec='k', markersize=ms,
                color=color, markerfacecolor=color2,
                label='_nolegend_')

    # Control
    ax.plot(fcst_x,
            HDWfcst[:, 0, lat, lon],
            linewidth=width+1, linestyle=style, marker='o',
            mec='k', markersize=ms,
            color='r')

    # TICKS: Present, +1, +2...
    max_show = min(6, len(x_all)) +1 # show up to day 6
    xtick_locs = list(x_all[:max_show])
    xtick_lbls = ['0'] + [f'+{i}' for i in range(1, max_show)]

    ax.set_xticks(xtick_locs)
    ax.set_xticklabels(xtick_lbls)

    for t in ax.get_xticklabels():
        t.set_color('black')

    ax.set_xlim(0, x_all[-1])
    ax.set_ylim(0, height)

        # --- Axis labels
    ax.set_ylabel("HDWI", fontsize=24, labelpad=15, weight='bold')
    ax.set_xlabel("Day", fontsize=24, labelpad=15, weight='bold')

    # --- Title (use ax.set_title OR figtext; set_title is simpler)
    ax.set_title(f"Max Daily HDWI\nGEFS Forecast {latvar[lat]:.1f}°N, {abs(lonvar[lon]):.1f}°W", fontsize=22, weight='bold', pad=12)


    # --- Tick sizes
    ax.tick_params(axis='x', labelsize=16)
    ax.tick_params(axis='y', labelsize=16)

 
# --- Legend (outside, right, vertical)
    handles, labels = ax.get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))




@app.route('/forecast')
def serve_forecast():
    lat = int(request.args.get('lat', 0))
    lon = int(request.args.get('lon', 0))

    directory_forecast = r'./'
    filename_forecast = r'GEFS_HDW_FCST.nc'
    directory_past = r'./'
    directory_climo = r'./'
    filename_climo = r'CFSR_MaxDHDW_CLIMO.nc'

    current_day = get_current_day()

    # CLIMATOLOGY
    ncfile = Dataset(directory_climo + filename_climo, 'r')
    climo = ncfile.variables['climoARRAY'][:]
    latvar = ncfile.variables['latitude'][:]
    lonvar = ncfile.variables['longitude'][:]
    ncfile.close()

    # FORECAST DATA
    ncfile_forecast = Dataset(directory_forecast + filename_forecast, 'r')
    HDWfcst = ncfile_forecast.variables['HDWI'][:]
    ncfile_forecast.close()

    # ANALYSIS DATA
    HDWpast = []
    for n in reversed(range(1, 11)):
        filename = f'GEFS_HDW_ANL_day-{n}.nc'
        try:
            ncfile = Dataset(directory_past + filename, 'r')
            HDWpast.append(ncfile.variables['HDWI'][:].data)
            ncfile.close()
        except OSError:
            HDWpast.append(np.full(shape=[len(latvar), len(lonvar)], fill_value=np.nan))
    HDWpast = np.asarray(HDWpast)

    fig = plt.figure(figsize=(21, 16))
    fcst_plot(fig, lat, lon, HDWpast[:, lat, lon], HDWfcst, climo, current_day, latvar, lonvar)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return send_file(buf, mimetype='image/png')


if __name__ == "__main__":
    app.run(port=5001)
