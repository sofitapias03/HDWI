import mplcursors as mplc
import numpy as np
from netCDF4 import Dataset
import datetime as dt

import cartopy.crs as ccrs 
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

import matplotlib.pyplot as plt
from matplotlib import cm

from pyproj import CRS, Transformer
from shapely.ops import transform

from cartopy.io import shapereader

from flask import Flask, send_file, send_from_directory
from flask_cors import CORS
import io
import os

app = Flask(__name__)
CORS(app)

cd_shp = r"censusDivisions/lcsd000b21a_e.shp"

reader = shapereader.Reader(cd_shp, encoding="latin1")

prj_path = cd_shp.replace(".shp", ".prj")
src_crs = CRS.from_wkt(open(prj_path, "r").read())
transformer = Transformer.from_crs(src_crs, CRS.from_epsg(4326), always_xy=True)

geoms_absk = []
for rec in reader.records():
    pruid = str(rec.attributes.get("PRUID", ""))
    if pruid in ("47", "48"):
        geoms_absk.append(transform(transformer.transform, rec.geometry))

canada_cd_feature = cfeature.ShapelyFeature(
    geoms_absk, ccrs.PlateCarree(),
    facecolor="none", edgecolor="black", linewidth=10
)

# get cartopy info
crs = ccrs.PlateCarree()
water = "#91B1FF"

states_provinces = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_1_states_provinces_lakes',
    scale='10m',
    facecolor='none')

lakes_50m = cfeature.NaturalEarthFeature('physical', 'lakes', '50m',
                                         edgecolor='black',
                                         facecolor=water)

rivers_50m = cfeature.NaturalEarthFeature('physical', 'rivers_lake_centerlines', '50m',
                                          facecolor='none',
                                          edgecolor='#91B1FF')

ocean_50m = cfeature.NaturalEarthFeature('physical', 'ocean', '50m',
                                         edgecolor='face',
                                         facecolor=water)

perc_levels = [0, 24, 49, 74, 89, 94, 100]
perc_levels_cbar = [0, 25, 50, 75, 90, 95, 100]
perc_colors = ['w', "#FBFC77", "#FFB866", "#FF2B6F", "#93099E", "#420347"]


def get_current_day():
    year = dt.date.today().year
    start_of_year = dt.date(year, 1, 1)
    today = dt.date.today()
    return (today - start_of_year).days


def get_grid(type, day, forecast_day, latvar, lonvar, HDWfcst, climo):
    grid = np.zeros([latvar, lonvar])
    day_climo = day + forecast_day

    for lat in range(0, latvar):
        for lon in range(0, lonvar):
            if type == 'max':
                val = max(HDWfcst[forecast_day, :, lat, lon])
            else:
                val = np.median(HDWfcst[forecast_day, :, lat, lon])
            if val != 'NaN':
                if val >= climo[0, day_climo, lat, lon]:
                    grid[lat, lon] = 25
                if val >= climo[1, day_climo, lat, lon]:
                    grid[lat, lon] = 50
                if val >= climo[2, day_climo, lat, lon]:
                    grid[lat, lon] = 75
                if val >= climo[3, day_climo, lat, lon]:
                    grid[lat, lon] = 90
                if val >= climo[4, day_climo, lat, lon]:
                    grid[lat, lon] = 96
            else:
                grid[lat, lon] = np.nan
    return grid


def make_map(grid_type, type_string, latvar, lonvar, directory_fig, day, name):
    fig = plt.figure(figsize=(43, 21), constrained_layout=True)

    proj = ccrs.LambertConformal(
        central_longitude=-110,
        central_latitude=55
    )

    ax = fig.add_subplot(111, projection=proj)
    ax.set_extent([-120, -101, 48, 61], crs=ccrs.PlateCarree())

    x, y = np.meshgrid(lonvar, latvar)
    cs = ax.contourf(
        x, y, grid_type,
        levels=perc_levels,
        colors=perc_colors,
        alpha=0.8,
        transform=ccrs.PlateCarree()
    )

    cbar = fig.colorbar(cs, ax=ax, orientation="vertical", fraction=0.035, pad=0.02)
    cbar.set_label("Percentile", fontsize=28, weight="bold")
    cbar.ax.tick_params(labelsize=22)

    cities = cfeature.NaturalEarthFeature(
        category="cultural", name="populated_places", scale="50m", facecolor="none"
    )
    ax.add_feature(cities, edgecolor="black", linewidth=0.5, zorder=40)
    ax.add_feature(states_provinces, edgecolor="k", alpha=1, linewidth=0.8, zorder=31)
    ax.add_feature(ocean_50m, zorder=30)
    ax.add_feature(rivers_50m, zorder=30)
    ax.add_feature(lakes_50m, zorder=30, linewidth=0.5)
    ax.coastlines(resolution="50m", color="black", linewidth=1, zorder=31)
    ax.add_feature(canada_cd_feature, linewidth=1.7, edgecolor="black", zorder=32)

    ax.set_title(
        (dt.date.today() + dt.timedelta(days=day)).strftime('%d %b %Y') + f" {type_string} HDWI Map",
        fontsize=42, weight="bold", pad=20
    )

    ax.text(
        0.015, 0.02,
        "Created " + dt.datetime.utcnow().strftime("%H%M UTC"),
        fontsize=24, ha="left", va="bottom",
        color="#21414c", transform=ax.transAxes, zorder=32, weight="bold"
    )

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=4, color='gray', alpha=0.5, linestyle='--')
    gl.xlocator = mticker.MultipleLocator(2.5)
    gl.ylocator = mticker.MultipleLocator(1)
    gl.xlabels_top = True
    gl.ylabels_right = True
    gl.xlabels_bottom = False
    gl.ylabels_left = False
    gl.inline_labels = False
    gl.rotate_labels = False
    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()
    gl.xlabel_style = {'size': 22, 'weight': 'bold'}
    gl.ylabel_style = {'size': 22, 'weight': 'bold'}

    return cs



@app.route('/map')
def serve_map():
    directory_climo = r'./'
    filename_climo = r'CFSR_MaxDHDW_CLIMO.nc'
    directory_forecast = r'./'
    filename_forecast = r'GEFS_HDW_FCST.nc'
    directory_fig = r'./maps/'

    os.makedirs(directory_fig, exist_ok=True)

    # Load climatology
    ncfile = Dataset(directory_climo + filename_climo, 'r')
    climo = ncfile.variables['climoARRAY'][:]
    latvar = ncfile.variables['latitude'][:]
    lonvar = ncfile.variables['longitude'][:]
    ncfile.close()

    # Load forecast
    ncfile_forecast = Dataset(directory_forecast + filename_forecast, 'r')
    HDWfcst = ncfile_forecast.variables['HDWI'][:]
    ncfile_forecast.close()

    today = dt.date.today()

    saved_files = []

    # 🔥 Loop through today + next 6 days
    for i in range(7):
        future_date = today + dt.timedelta(days=i)

        # Correct day-of-year for each future day
        day_of_year = (future_date - dt.date(future_date.year, 1, 1)).days

        # Generate grid + map
        grid_max = get_grid('max', day_of_year, i, len(latvar), len(lonvar), HDWfcst, climo)
        make_map(grid_max, 'Max', latvar, lonvar, directory_fig, i, 'maxMap_day_')

        filename = f"{directory_fig}maxMap_day_{i}.png"

        # Save figure
        plt.savefig(filename, dpi=200, bbox_inches='tight')
        plt.close()

        saved_files.append({
            "day_index": i,
            "date": future_date.isoformat(),
            "file": filename
        })

    return {
        "message": "Maps generated successfully",
        "maps": saved_files
    }

@app.route("/maps/<filename>")
def serve_map_file(filename):
    # assuming your maps folder is inside the Flask directory
    map_dir = os.path.join(os.getcwd(), "maps")
    return send_from_directory(map_dir, filename)


# @app.route('/map')
# def serve_map():
#     directory_climo = r'./'
#     filename_climo = r'CFSR_MaxDHDW_CLIMO.nc'
#     directory_forecast = r'./'
#     filename_forecast = r'GEFS_HDW_FCST.nc'
#     directory_fig = r'./'

#     ncfile = Dataset(directory_climo + filename_climo, 'r')
#     climo = ncfile.variables['climoARRAY'][:]
#     latvar = (ncfile.variables['latitude'][:])
#     lonvar = (ncfile.variables['longitude'][:])
#     ncfile.close()

#     ncfile_forecast = Dataset(directory_forecast + filename_forecast, 'r')
#     HDWfcst = ncfile_forecast.variables['HDWI'][:]
#     ncfile_forecast.close()

#     current_day = get_current_day() 

#     # Only generate i=0 (today's max map)
#     grid_max = get_grid('max', current_day, 0, len(latvar), len(lonvar), HDWfcst, climo)
#     cs_max = make_map(grid_max, 'Max', latvar, lonvar, directory_fig, 0, 'maxMap_day_')
# #added comment
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')    
#     buf.seek(0)
#     plt.close()
#     return send_file(buf, mimetype='image/png')

    
if __name__ == "__main__":
    app.run(port=5050)