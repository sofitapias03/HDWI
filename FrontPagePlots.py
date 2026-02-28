from ast import main
import mplcursors as mplc
import numpy as np
from netCDF4 import Dataset
import datetime as dt
import time


import cartopy.crs as ccrs 
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter


import matplotlib.pyplot as plt
from matplotlib import cm

from pyproj import CRS, Transformer
from shapely.ops import transform


import cartopy.crs as ccrs 
import cartopy.feature as cfeature
import matplotlib.ticker as mticker

import matplotlib.pyplot as plt
from matplotlib import cm
from cartopy.io import shapereader
from pyproj import Transformer
from shapely.ops import transform
import cartopy.feature as cfeature
import cartopy.crs as ccrs

cd_shp = r"censusDivisions\lcd_000b21a_e.shp"

reader = shapereader.Reader(cd_shp, encoding="latin1")

# If the shapefile CRS is already EPSG:4326 you can skip reprojection entirely.
# But since you're reading WKT from .prj, keep your transformer approach:
from pyproj import CRS
prj_path = cd_shp.replace(".shp", ".prj")
src_crs = CRS.from_wkt(open(prj_path, "r").read())
transformer = Transformer.from_crs(src_crs, CRS.from_epsg(4326), always_xy=True)

geoms_absk = []
for rec in reader.records():
    # Adjust field name if needed (print(rec.attributes.keys()))
    pruid = str(rec.attributes.get("PRUID", ""))
    if pruid in ("47", "48"):        # SK, AB
        geoms_absk.append(transform(transformer.transform, rec.geometry))

canada_cd_feature = cfeature.ShapelyFeature(
    geoms_absk, ccrs.PlateCarree(),
    facecolor="none", edgecolor="black", linewidth=10
)




#grabs the current day automatically
def get_current_day():
    year = dt.date.today().year #get this year
    start_of_year = dt.date(year, 1, 1) #get jan 1st
    today = dt.date.today()  #get today

    return (today - start_of_year).days #return distance from jan 1


def get_grid(type,#max or median
                         day,#how far from current day
                         forecast_day, #int representing day in the year
                           latvar, lonvar, HDWfcst, climo):
    # create grid of zeroes
    grid = np.zeros([latvar,lonvar])
    day_climo = day + forecast_day

    # fill grid based on highest percentile that max current day forecast exceeds
    for lat in range(0,latvar):
        for lon in range(0,lonvar):
            if type == 'max':
                val = max(HDWfcst[forecast_day,:,lat,lon]) #get the max value from HDW values for today

            else:
                 val = np.median(HDWfcst[forecast_day,:,lat,lon])
            if val != 'NaN':
                if val >= climo[0,day_climo,lat,lon]:
                    grid[lat,lon]  = 25
                if val >= climo[1,day_climo,lat,lon]:
                    grid[lat,lon]  = 50
                if val >= climo[2,day_climo,lat,lon]:
                    grid[lat,lon]  = 75
                if val >= climo[3,day_climo,lat,lon]:
                    grid[lat,lon]  = 90
                if val >= climo[4,day_climo ,lat,lon]:
                    grid[lat,lon]  = 96
            else:
                grid[lat,lon] = 'NaN'
    return grid


# get cartopy info
crs = ccrs.PlateCarree() #cordinate reference system
water = "#91B1FF"#'#8AABFF'

states_provinces = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lakes',
        scale='10m',
        facecolor='none')

lakes_50m = cfeature.NaturalEarthFeature('physical', 'lakes', '50m',
                                        edgecolor='black',
                                        facecolor=water)

rivers_50m = cfeature.NaturalEarthFeature('physical', 'rivers_lake_centerlines', '50m', facecolor='none',
                                         edgecolor='#91B1FF')
ocean_50m = cfeature.NaturalEarthFeature('physical', 'ocean', '50m',
                                        edgecolor='face',
                                        facecolor=water)
# get plot info
perc_levels = [0,24,49,74,89,94,100]
perc_levels_cbar = [0,25,50,75,90,95,100]
perc_colors = ['w',
               "#FBFC77",
                "#FFB866",
                "#FF2B6F",
                "#93099E",
                "#420347"]

def plot_CONUS():
    directory_climo = r'./'
    filename_climo = r'CFSR_MaxDHDW_CLIMO.nc'
    directory_forecast = r'./'
    filename_forecast = r'GEFS_HDW_FCST.nc'
    directory_fig = r'./'

    ncfile = Dataset(directory_climo + filename_climo, 'r')
    climo = ncfile.variables['climoARRAY'][:]
    latvar = (ncfile.variables['latitude'][:])
    lonvar = (ncfile.variables['longitude'][:])
    ncfile.close()

    ncfile_forecast = Dataset(directory_forecast + filename_forecast, 'r')
    HDWfcst = ncfile_forecast.variables['HDWI'][:]
    ncfile_forecast.close()

    current_day = get_current_day()

    def custom_format_coord(x, y):
        lon, lat = ccrs.PlateCarree().transform_point(x, y, cs_max.axes.projection)
        lat_idx = np.argmin(np.abs(latvar - lat))
        lon_idx = np.argmin(np.abs(lonvar - lon))
        val = grid_max[lat_idx, lon_idx]
        return f"Lat: {lat:.7f}°  Lon: {lon:.7f}°"


    for i in range(0,5):
            grid_max = get_grid('max', current_day, i, len(latvar), len(lonvar), HDWfcst, climo)
            cs_max = make_map(grid_max, 'Max', latvar, lonvar, directory_fig, i, f'maxMap_day_')
    
            grid_median = get_grid('median', current_day, i, len(latvar), len(lonvar), HDWfcst, climo)
            cs_median = make_map(grid_median, 'Median', latvar, lonvar, directory_fig, i, f'medianMap_day_')

            cs_max.axes.format_coord = custom_format_coord
            cs_median.axes.format_coord = custom_format_coord

            plt.show()

    cs_max.axes.format_coord = custom_format_coord

    plt.show()


######################################################################################3

def make_map(grid_type, type_string, latvar, lonvar, directory_fig, day, name):

    fig = plt.figure(figsize=(16, 8), constrained_layout=True)

    proj = ccrs.LambertConformal(
        central_longitude=-110,
        central_latitude=55
    )

    ax = fig.add_subplot(111, projection=proj)
    # Map axis on the right
    ax.set_extent([-120, -101, 48, 61], crs=ccrs.PlateCarree())

    # Plot the field
    x, y = np.meshgrid(lonvar, latvar)
    cs = ax.contourf(
        x, y, grid_type,
        levels=perc_levels,
        colors=perc_colors,
        alpha=0.8,
        transform=ccrs.PlateCarree()
    )

        # Colorbar (vertical, left)
    cbar = fig.colorbar(
        cs,
        ax=ax,
        orientation="vertical",
        fraction=0.035,
        pad=0.02
    )
    cbar.set_label("Percentile", fontsize=14)
    cbar.ax.tick_params(labelsize=12)

    # Optional: if you want the colorbar to be the only thing visible in that left panel
    # (removes extra frame/ticks around the colorbar axis)



    # Cities layer (can be heavy; 50m is okay)
    cities = cfeature.NaturalEarthFeature(
        category="cultural",
        name="populated_places",
        scale="50m",
        facecolor="none"
    )
    ax.add_feature(cities, edgecolor="black", linewidth=0.5, zorder=40)

    # Land/water + boundaries
    ax.add_feature(states_provinces, edgecolor="k", alpha=1, linewidth=0.8, zorder=31)
    ax.add_feature(ocean_50m, zorder=30)
    ax.add_feature(rivers_50m, zorder=30)
    ax.add_feature(lakes_50m, zorder=30, linewidth=0.5)


    # ax.add_feature(USCOUNTIES.with_scale('20m'), linewidth=0.1, edgecolor='k')

    ax.coastlines(resolution="50m", color="black", linewidth=1, zorder=31)
    ax.add_feature(canada_cd_feature, linewidth=0.5, edgecolor="black", zorder=32)

    # Title + timestamp (attach title to the map axis)
    todays_date = dt.date.today().strftime("%d %b %Y ")
    ax.set_title(
        (dt.date.today() + dt.timedelta(days=day)).strftime('%d %b %Y') + f" {type_string} HDWI Map",
        fontsize=22,
        weight="bold",
        pad=12
    )

    ax.text(
        0.015, 0.02,
        "Created " + dt.datetime.utcnow().strftime("%H%M UTC"),
        fontsize=14,
        ha="left", va="bottom",
        color="#21414c",
        transform=ax.transAxes,
        zorder=32,
        weight="bold"
    )

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlocator = mticker.MultipleLocator(2.5)
    gl.ylocator = mticker.MultipleLocator(1)

    # Customize the labels
    gl.xlabels_top = True #rn off labels on the top
    gl.ylabels_right = True # Turn off labels on the right
    gl.xlabels_bottom = False
    gl.ylabels_left = False
    gl.inline_labels = False
    gl.rotate_labels = False
    
    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()

    #shows figure and saves it
    return cs


def main():
    plot_CONUS()

if __name__ == "__main__":
    main()