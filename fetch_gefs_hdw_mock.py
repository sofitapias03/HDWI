import numpy as np
from netCDF4 import Dataset
import datetime as dt
import argparse

def build_gefs_hdw_nc_mock(run_date, out_path="GEFS_HDW_FCST.nc"):
    """
    Create a mock GEFS_HDW_FCST.nc file with realistic structure but fake data.
    This lets you test the plotting pipeline without needing eccodes installed.
    """
    
    LAT_MIN, LAT_MAX, LAT_STEP = 20.0, 60.0, 0.5
    LON_MIN, LON_MAX, LON_STEP = -130.0, -60.0, 0.5
    
    out_lats = np.arange(LAT_MIN, LAT_MAX + LAT_STEP/2, LAT_STEP, dtype=np.float32)
    out_lons = np.arange(LON_MIN, LON_MAX + LON_STEP/2, LON_STEP, dtype=np.float32)
    n_lat, n_lon = len(out_lats), len(out_lons)
    
    N_DAYS, N_MEMBERS = 7, 21
    
    # Generate realistic random data
    np.random.seed(42)
    hdwi_out = np.random.uniform(0, 100, (N_DAYS, N_MEMBERS, n_lat, n_lon)).astype(np.float32)
    u_out = np.random.uniform(0, 20, (N_DAYS, N_MEMBERS, n_lat, n_lon)).astype(np.float32)
    vpd_out = np.random.uniform(0, 10, (N_DAYS, N_MEMBERS, n_lat, n_lon)).astype(np.float32)
    
    # Write NetCDF
    nc = Dataset(out_path, "w", format="NETCDF4")
    
    nc.createDimension("day", N_DAYS)
    nc.createDimension("member", N_MEMBERS)
    nc.createDimension("latitude", n_lat)
    nc.createDimension("longitude", n_lon)
    
    lat_v = nc.createVariable("latitude", "f4", ("latitude",))
    lat_v.units = "degrees_north"
    lat_v[:] = out_lats
    
    lon_v = nc.createVariable("longitude", "f4", ("longitude",))
    lon_v.units = "degrees_east"
    lon_v[:] = out_lons
    
    hdw_v = nc.createVariable("HDWI", "f4", ("day", "member", "latitude", "longitude"))
    hdw_v.units = "HDW"
    hdw_v[:] = hdwi_out
    
    u_v = nc.createVariable("U", "f4", ("day", "member", "latitude", "longitude"))
    u_v.units = "m/s"
    u_v[:] = u_out
    
    vpd_v = nc.createVariable("VPD", "f4", ("day", "member", "latitude", "longitude"))
    vpd_v.units = "hPa"
    vpd_v[:] = vpd_out
    
    nc.run_date = run_date.strftime("%Y%m%d")
    nc.created = dt.datetime.utcnow().isoformat()
    
    nc.close()
    print(f"[✓] Mock GEFS file created: {out_path}")
    print(f"    Shape: day(7) × member(21) × latitude(81) × longitude(141)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None)
    parser.add_argument("--out", default="GEFS_HDW_FCST.nc")
    args = parser.parse_args()
    
    if args.date:
        run_date = dt.datetime.strptime(args.date, "%Y%m%d").date()
    else:
        run_date = dt.date.today()
    
    build_gefs_hdw_nc_mock(run_date, args.out)