import numpy as np
from netCDF4 import Dataset
import datetime as dt
import os

import cartopy.crs as ccrs 
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import matplotlib.pyplot as plt

from pyproj import CRS, Transformer
from shapely.ops import transform
from cartopy.io import shapereader

# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP CARTOGRAPHY
# ═══════════════════════════════════════════════════════════════════════════════

cd_shp = r"censusDivisions/lcsd000b21a_e.shp"

HAS_CANADA_SHAPES = False
try:
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
    HAS_CANADA_SHAPES = True
    print("[✓] Loaded Canada census division shapes")
except Exception as e:
    print(f"[⚠] Could not load census divisions: {e}")
    print("    Maps will still be generated without Canada shapes")

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
perc_colors = ['w', "#FBFC77", "#FFB866", "#FF2B6F", "#93099E", "#420347"]


# ═══════════════════════════════════════════════════════════════════════════════
#  GRID GENERATION (EXACT COPY FROM FrontPagePlots.py)
# ═══════════════════════════════════════════════════════════════════════════════

def get_grid(type, day, forecast_day, latvar, lonvar, HDWfcst, climo):
    """Generate percentile grid for a given day."""
    grid = np.zeros([latvar, lonvar])
    day_climo = day + forecast_day

    for lat in range(0, latvar):
        for lon in range(0, lonvar):
            if type == 'max':
                # FIX: Use nanmax instead of max to handle NaN values safely
                val = np.nanmax(HDWfcst[forecast_day, :, lat, lon])
            else:
                val = np.nanmedian(HDWfcst[forecast_day, :, lat, lon])
            
            if not np.isnan(val):
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


# ═══════════════════════════════════════════════════════════════════════════════
#  MAP GENERATION (EXACT COPY FROM FrontPagePlots.py)
# ═══════════════════════════════════════════════════════════════════════════════

def make_map(grid_type, type_string, latvar, lonvar, day):
    """Create and return a map figure."""
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

    # Add features
    cities = cfeature.NaturalEarthFeature(
        category="cultural", name="populated_places", scale="50m", facecolor="none"
    )
    ax.add_feature(cities, edgecolor="black", linewidth=0.5, zorder=40)
    ax.add_feature(states_provinces, edgecolor="k", alpha=1, linewidth=0.8, zorder=31)
    ax.add_feature(ocean_50m, zorder=30)
    ax.add_feature(rivers_50m, zorder=30)
    ax.add_feature(lakes_50m, zorder=30, linewidth=0.5)
    ax.coastlines(resolution="50m", color="black", linewidth=1, zorder=31)
    
    if HAS_CANADA_SHAPES:
        ax.add_feature(canada_cd_feature, linewidth=1.7, edgecolor="black", zorder=32)

    # Title
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

    # Gridlines
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

    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════════

def generate_all_maps(climo_path="./CFSR_MaxDHDW_CLIMO.nc",
                      forecast_path="./GEFS_HDW_FCST.nc",
                      output_dir="./maps"):
    """Generate forecast maps for the next 7 days."""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading climatology...")
    ncfile_climo = Dataset(climo_path, 'r')
    climo = ncfile_climo.variables['climoARRAY'][:]
    latvar = ncfile_climo.variables['latitude'][:]
    lonvar = ncfile_climo.variables['longitude'][:]
    ncfile_climo.close()
    
    print("Loading forecast...")
    ncfile_forecast = Dataset(forecast_path, 'r')
    HDWfcst = ncfile_forecast.variables['HDWI'][:]
    ncfile_forecast.close()
    
    today = dt.date.today()
    
    print(f"\nGenerating maps for {today} + 6 days...\n")
    
    # Generate 7 daily maps (exact loop from FrontPagePlots.py)
    for i in range(7):
        future_date = today + dt.timedelta(days=i)
        day_of_year = (future_date - dt.date(future_date.year, 1, 1)).days
        
        print(f"  Day {i}: {future_date.strftime('%Y-%m-%d')}", end=" ... ", flush=True)
        
        # Generate grid
        grid_max = get_grid('max', day_of_year, i, len(latvar), len(lonvar), 
                           HDWfcst, climo)
        
        # Create map
        fig = make_map(grid_max, 'Max', latvar, lonvar, i)
        
        # Save
        filename = os.path.join(output_dir, f"maxMap_day_{i}.png")
        plt.savefig(filename, dpi=200, bbox_inches='tight')
        plt.close(fig)
        
        print("✓")
    
    print(f"\n[✓] Maps saved to {output_dir}/")


if __name__ == "__main__":
    generate_all_maps()