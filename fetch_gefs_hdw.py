"""
fetch_gefs_hdw.py
-----------------
Downloads GEFS 0000 UTC ensemble forecast data from NOMADS/NCEI and computes
the Hot-Dry-Windy Index (HDW) for each forecast day and ensemble member,
producing a NetCDF file whose structure matches GEFS_HDW_FCST.nc exactly:

  Dimensions : day(7), member(21), latitude(81), longitude(141)
  Variables  : latitude, longitude, HDWI, U, VPD
  Domain     : 20–60 °N, 130–60 °W  (0.5° grid, matching the sample file)

HDW methodology (Srock et al. 2018, doi:10.3390/atmos9070279)
--------------------------------------------------------------
  HDW = max_wind_speed  ×  max_VPD
where both maxima are taken over the lowest ~500 m (lowest 50 hPa) of the
atmosphere for each 3-hourly GEFS time-step between 1200 and 0300 UTC
(i.e., the local daytime window for North America).
VPD = es(T) − e(Td)  in hPa, surface-pressure adjusted to sea-level.

Usage
-----
  python fetch_gefs_hdw.py                  # uses today's 00z GEFS run
  python fetch_gefs_hdw.py --date 20260415  # specific run date (YYYYMMDD)
  python fetch_gefs_hdw.py --out my_file.nc # custom output path

Dependencies
------------
  pip install requests numpy netCDF4 cfgrib eccodes xarray
  (cfgrib/eccodes needed for reading GRIB2 from NOMADS)
"""

import argparse
import datetime as dt
import os
import sys
import requests
import numpy as np
from netCDF4 import Dataset

# ── optional: use xarray+cfgrib if available, otherwise fall back to pygrib ──
try:
    import xarray as xr
    import cfgrib  # noqa – registers xarray backend
    USE_XARRAY = True
except ImportError:
    USE_XARRAY = False
    try:
        import pygrib
    except ImportError:
        sys.exit(
            "Install either 'xarray + cfgrib + eccodes'  OR  'pygrib'.\n"
            "  pip install cfgrib eccodes xarray   (recommended)\n"
            "  pip install pygrib                  (alternative)"
        )

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Output grid — must match the sample .nc file exactly
LAT_MIN, LAT_MAX, LAT_STEP = 20.0,  60.0, 0.5   # 81 points
LON_MIN, LON_MAX, LON_STEP = -130.0, -60.0, 0.5  # 141 points

N_DAYS    = 7    # forecast days (day 1 … day 7)
N_MEMBERS = 21   # 1 control + 20 perturbed members

# GEFS 3-hourly forecast hours that fall in the 1200–0300 UTC daytime window
# for each day D (hours since 00z of run day):
#   Day 1: f012, f015, f018, f021, f024  → hrs 12,15,18,21,24
#   Day 2: f036, f039, f042, f045, f048  → hrs 36,39,42,45,48  etc.
# We collect every 3-h step from f003 onward; the window selection is done
# after download when computing the daily maximum.
DAYTIME_OFFSETS = [12, 15, 18, 21]   # offsets within each 24-h block (hours)

# NOMADS OPeNDAP base URL for current GEFS runs (last ~10 days)
NOMADS_BASE = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gens/prod"

# NCEI archive URL for older GEFS runs (>10 days old)
# Requires Earthdata login; see note below.
NCEI_BASE = "https://www.ncei.noaa.gov/data/global-ensemble-forecast-system/access"

# Pressure levels (hPa) typically available in GEFS pgrb2 files.
# We use surface (10-m wind, 2-m T/Td) plus the lowest few pressure levels
# to approximate the lowest 50 hPa (~500 m) column.
PRESSURE_LEVELS = [1000, 975, 950, 925]   # hPa; add 850 if surface is ~850 hPa

# ═══════════════════════════════════════════════════════════════════════════════
#  SATURATION VAPOR PRESSURE (hPa)   Magnus formula
# ═══════════════════════════════════════════════════════════════════════════════

def sat_vp(T_c: np.ndarray) -> np.ndarray:
    """Saturation vapor pressure (hPa) from temperature in °C."""
    return 6.112 * np.exp(17.67 * T_c / (T_c + 243.5))


def vpd_from_T_Td(T_c: np.ndarray, Td_c: np.ndarray) -> np.ndarray:
    """VPD (hPa) = es(T) − e(Td)."""
    es = sat_vp(T_c)
    e  = sat_vp(Td_c)
    return np.maximum(es - e, 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
#  NOMADS URL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def nomads_url(run_date: dt.date, member: int, fhour: int) -> str:
    """
    Build the NOMADS URL for a single GEFS member and forecast hour.

    GEFS file naming on NOMADS (as of 2024):
      gefs.YYYYMMDD/00/atmos/pgrb2sp25/
        gec00.t00z.pgrb2s.0p25.fHHH   (control)
        gep01.t00z.pgrb2s.0p25.fHHH   (perturbed 01–20)

    The "pgrb2s" ("slim") files contain the most-used variables including
    TMP, DPT, UGRD, VGRD at surface and pressure levels.
    """
    datestr = run_date.strftime("%Y%m%d")
    fstr    = f"{fhour:03d}"
    if member == 0:
        fname = f"gec00.t00z.pgrb2s.0p25.f{fstr}"
    else:
        fname = f"gep{member:02d}.t00z.pgrb2s.0p25.f{fstr}"

    url = (
        f"{NOMADS_BASE}/gefs.{datestr}/00/atmos/pgrb2sp25/{fname}"
    )
    return url


def wgrib2_subset_url(base_url: str) -> str:
    """
    Append a NOMADS filter query to download only the variables we need,
    reducing bandwidth dramatically.

    Variables required:
      TMP    : temperature at 2 m and pressure levels (for VPD via es)
      DPT    : dew-point at 2 m and pressure levels (for e)
      UGRD, VGRD: u/v wind at 10 m and pressure levels
      HGT    : geopotential height at pressure levels (to ID lowest 50 hPa)
      PRES   : surface pressure (to anchor the 50-hPa column)
    """
    # NOMADS HTTP filter service — append to the GRIB2 path
    filter_base = base_url.replace(
        NOMADS_BASE,
        "https://nomads.ncep.noaa.gov/cgi-bin/filter_gefs_atmos_0p25s.pl?file="
        + os.path.basename(base_url)
    )
    params = (
        "&var_TMP=on&var_DPT=on&var_UGRD=on&var_VGRD=on"
        "&var_HGT=on&var_PRES=on"
        "&lev_2_m_above_ground=on&lev_10_m_above_ground=on"
        "&lev_surface=on"
        "&lev_1000_mb=on&lev_975_mb=on&lev_950_mb=on&lev_925_mb=on"
        f"&leftlon={int(LON_MIN+360)}&rightlon={int(LON_MAX+360)}"
        f"&toplat={int(LAT_MAX)}&bottomlat={int(LAT_MIN)}"
        "&dir=%2Fgefs." + run_date.strftime("%Y%m%d") + "%2F00%2Fatmos%2Fpgrb2sp25"
    )
    return filter_base + params


# ═══════════════════════════════════════════════════════════════════════════════
#  DOWNLOAD HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def download_grib(url: str, local_path: str, timeout: int = 120) -> bool:
    """Download a GRIB2 file; returns True on success."""
    if os.path.exists(local_path):
        return True   # already cached
    print(f"  Downloading {os.path.basename(local_path)} …", end=" ", flush=True)
    try:
        r = requests.get(url, timeout=timeout, stream=True)
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        print("OK")
        return True
    except Exception as exc:
        print(f"FAILED ({exc})")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  GRIB READING  (xarray/cfgrib path)
# ═══════════════════════════════════════════════════════════════════════════════

def read_grib_xarray(path: str):
    """
    Read a GRIB2 file with xarray/cfgrib.
    Returns a dict: {'TMP_sfc': array, 'DPT_sfc': array,
                     'UGRD_sfc': array, 'VGRD_sfc': array,
                     'TMP_pres': {level: array}, ...}
    All arrays are on the LAT/LON output grid.
    """
    out_lats = np.arange(LAT_MIN, LAT_MAX + LAT_STEP/2, LAT_STEP)
    out_lons = np.arange(LON_MIN, LON_MAX + LON_STEP/2, LON_STEP)

    result = {}

    # ── surface / near-surface fields ──────────────────────────────────────────
    try:
        ds_sfc = xr.open_dataset(
            path, engine="cfgrib",
            filter_by_keys={"typeOfLevel": "heightAboveGround"},
            indexpath=None
        )
        # 2-m temperature & dew point
        if "t2m" in ds_sfc:
            result["TMP_sfc"] = _regrid(ds_sfc["t2m"].values - 273.15,
                                        ds_sfc["latitude"].values,
                                        ds_sfc["longitude"].values,
                                        out_lats, out_lons)
        if "d2m" in ds_sfc:
            result["DPT_sfc"] = _regrid(ds_sfc["d2m"].values - 273.15,
                                        ds_sfc["latitude"].values,
                                        ds_sfc["longitude"].values,
                                        out_lats, out_lons)
        ds_sfc.close()
    except Exception as e:
        print(f"    [warn] surface fields: {e}")

    # 10-m wind
    try:
        ds_wind = xr.open_dataset(
            path, engine="cfgrib",
            filter_by_keys={"typeOfLevel": "heightAboveGround",
                             "shortName": "10u"},
            indexpath=None
        )
        u10 = _regrid(ds_wind["u10"].values,
                      ds_wind["latitude"].values, ds_wind["longitude"].values,
                      out_lats, out_lons)
        ds_wind.close()

        ds_wind2 = xr.open_dataset(
            path, engine="cfgrib",
            filter_by_keys={"typeOfLevel": "heightAboveGround",
                             "shortName": "10v"},
            indexpath=None
        )
        v10 = _regrid(ds_wind2["v10"].values,
                      ds_wind2["latitude"].values, ds_wind2["longitude"].values,
                      out_lats, out_lons)
        ds_wind2.close()
        result["WSPD_sfc"] = np.sqrt(u10**2 + v10**2)
    except Exception as e:
        print(f"    [warn] 10-m wind: {e}")

    # ── pressure-level fields ──────────────────────────────────────────────────
    for short, key_out in [("t", "TMP"), ("dpt", "DPT")]:
        try:
            ds_p = xr.open_dataset(
                path, engine="cfgrib",
                filter_by_keys={"typeOfLevel": "isobaricInhPa",
                                 "shortName": short},
                indexpath=None
            )
            levels = ds_p["isobaricInhPa"].values
            result[f"{key_out}_pres"] = {}
            for lv in levels:
                if lv in PRESSURE_LEVELS:
                    arr = ds_p.sel(isobaricInhPa=lv)[
                        list(ds_p.data_vars)[0]].values
                    if key_out == "TMP":
                        arr = arr - 273.15
                    result[f"{key_out}_pres"][int(lv)] = _regrid(
                        arr,
                        ds_p["latitude"].values, ds_p["longitude"].values,
                        out_lats, out_lons
                    )
            ds_p.close()
        except Exception as e:
            print(f"    [warn] {key_out} pressure levels: {e}")

    # pressure-level winds → wind speed
    try:
        for comp, short in [("U", "u"), ("V", "v")]:
            ds_p = xr.open_dataset(
                path, engine="cfgrib",
                filter_by_keys={"typeOfLevel": "isobaricInhPa",
                                 "shortName": short},
                indexpath=None
            )
            levels = ds_p["isobaricInhPa"].values
            result[f"{comp}_pres"] = {}
            for lv in levels:
                if lv in PRESSURE_LEVELS:
                    arr = list(ds_p.data_vars.values())[0].sel(
                        isobaricInhPa=lv).values
                    result[f"{comp}_pres"][int(lv)] = _regrid(
                        arr,
                        ds_p["latitude"].values, ds_p["longitude"].values,
                        out_lats, out_lons
                    )
            ds_p.close()

        # combine U/V → speed at each level
        result["WSPD_pres"] = {}
        for lv in PRESSURE_LEVELS:
            if lv in result.get("U_pres", {}) and lv in result.get("V_pres", {}):
                result["WSPD_pres"][lv] = np.sqrt(
                    result["U_pres"][lv]**2 + result["V_pres"][lv]**2
                )
    except Exception as e:
        print(f"    [warn] pressure-level wind: {e}")

    return result, out_lats, out_lons


def _regrid(data: np.ndarray, src_lats, src_lons,
            dst_lats, dst_lons) -> np.ndarray:
    """
    Nearest-neighbor re-grid from source to destination lat/lon grid.
    GEFS 0.25° → our 0.5° grid (simple subsampling / nearest-neighbor).
    """
    # Handle longitude convention (0–360 → −180–180)
    src_lons = np.where(src_lons > 180, src_lons - 360, src_lons)

    out = np.full((len(dst_lats), len(dst_lons)), np.nan, dtype=np.float32)
    for i, lat in enumerate(dst_lats):
        ii = np.argmin(np.abs(src_lats - lat))
        for j, lon in enumerate(dst_lons):
            jj = np.argmin(np.abs(src_lons - lon))
            out[i, j] = data[ii, jj]
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  HDW CALCULATION FOR ONE GRIB FILE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_hdw_from_fields(fields: dict):
    """
    Given the dict returned by read_grib_*, compute:
      max_wind (m/s) and max_VPD (hPa) across the lowest-50-hPa column.

    The HDW methodology:
      1. Compute VPD at each level (surface + pressure levels up to 50 hPa
         above surface, approximated here as the 4 lowest available levels).
      2. Compute wind speed at each level.
      3. Take the maximum of each across the column.
      4. HDW = max_wind × max_VPD
    """
    shape = None
    all_wspd = []
    all_vpd  = []

    # surface / 2-m / 10-m
    if "TMP_sfc" in fields and "DPT_sfc" in fields:
        vpd_s = vpd_from_T_Td(fields["TMP_sfc"], fields["DPT_sfc"])
        all_vpd.append(vpd_s)
        shape = vpd_s.shape
    if "WSPD_sfc" in fields:
        all_wspd.append(fields["WSPD_sfc"])
        shape = fields["WSPD_sfc"].shape

    # pressure levels
    for lv in PRESSURE_LEVELS:
        if ("TMP_pres" in fields and lv in fields["TMP_pres"] and
                "DPT_pres" in fields and lv in fields["DPT_pres"]):
            vpd_p = vpd_from_T_Td(fields["TMP_pres"][lv], fields["DPT_pres"][lv])
            all_vpd.append(vpd_p)
            if shape is None:
                shape = vpd_p.shape
        if "WSPD_pres" in fields and lv in fields["WSPD_pres"]:
            all_wspd.append(fields["WSPD_pres"][lv])

    if not all_vpd or not all_wspd or shape is None:
        n_lat = len(np.arange(LAT_MIN, LAT_MAX + LAT_STEP/2, LAT_STEP))
        n_lon = len(np.arange(LON_MIN, LON_MAX + LON_STEP/2, LON_STEP))
        empty = np.zeros((n_lat, n_lon), dtype=np.float32)
        return empty, empty

    max_vpd  = np.maximum.reduce(all_vpd).astype(np.float32)
    max_wspd = np.maximum.reduce(all_wspd).astype(np.float32)
    return max_wspd, max_vpd


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════════

def build_gefs_hdw_nc(run_date: dt.date, out_path: str,
                      cache_dir: str = "./gefs_cache"):
    """
    Full pipeline:
      1. For each forecast day (1–7) and each GEFS member (0–20):
           - Download 3-hourly GRIB2 files in the 1200–0300 UTC window
           - Compute HDW at each time step
           - Take daily maximum of wind, VPD, and HDW
      2. Write the daily-max arrays to a NetCDF file matching
         the structure of GEFS_HDW_FCST.nc.
    """
    os.makedirs(cache_dir, exist_ok=True)

    out_lats = np.arange(LAT_MIN, LAT_MAX + LAT_STEP/2, LAT_STEP, dtype=np.float32)
    out_lons = np.arange(LON_MIN, LON_MAX + LON_STEP/2, LON_STEP, dtype=np.float32)
    n_lat, n_lon = len(out_lats), len(out_lons)

    # Output arrays: (day, member, lat, lon)
    hdwi_out = np.full((N_DAYS, N_MEMBERS, n_lat, n_lon), np.nan, dtype=np.float32)
    u_out    = np.zeros((N_DAYS, N_MEMBERS, n_lat, n_lon), dtype=np.float32)
    vpd_out  = np.zeros((N_DAYS, N_MEMBERS, n_lat, n_lon), dtype=np.float32)

    # ── GEFS forecast hours that correspond to each day's daytime window ───────
    # Day 1 → f012..f024; Day 2 → f036..f048; Day D → f(D*24-12)..f(D*24)
    # We grab the 1200, 1500, 1800, 2100 UTC timesteps of each forecast day
    # (i.e. hours 12,15,18,21 within that calendar day in UTC).

    for day_idx in range(N_DAYS):
        day_num = day_idx + 1   # 1-based
        # UTC hours since 00z run start for the 12–21z window of forecast day D
        fhours = [day_num * 24 - 12,   # 12z of that day
                  day_num * 24 - 9,    # 15z
                  day_num * 24 - 6,    # 18z
                  day_num * 24 - 3]    # 21z

        print(f"\n── Day {day_num} (f{fhours[0]:03d}–f{fhours[-1]:03d}) ──")

        for mem_idx in range(N_MEMBERS):
            print(f"  Member {mem_idx:02d}", end="")

            # Per-timestep maxima collectors for this member/day
            day_u   = []
            day_vpd = []

            for fh in fhours:
                fname = (f"gec00_f{fh:03d}.grb2" if mem_idx == 0
                         else f"gep{mem_idx:02d}_f{fh:03d}.grb2")
                local  = os.path.join(cache_dir,
                                      run_date.strftime("%Y%m%d"), fname)
                os.makedirs(os.path.dirname(local), exist_ok=True)

                url = nomads_url(run_date, mem_idx, fh)
                ok  = download_grib(url, local)
                if not ok:
                    continue

                try:
                    if USE_XARRAY:
                        fields, _, _ = read_grib_xarray(local)
                    else:
                        # pygrib fallback would go here; left as exercise
                        raise NotImplementedError("pygrib path not implemented")

                    wspd, vpd = compute_hdw_from_fields(fields)
                    day_u.append(wspd)
                    day_vpd.append(vpd)
                except Exception as exc:
                    print(f"\n    [error] fh={fh}: {exc}")

            if day_u and day_vpd:
                max_u   = np.maximum.reduce(day_u).astype(np.float32)
                max_vpd = np.maximum.reduce(day_vpd).astype(np.float32)
                u_out[day_idx,   mem_idx] = max_u
                vpd_out[day_idx, mem_idx] = max_vpd
                hdwi_out[day_idx, mem_idx] = max_u * max_vpd
            else:
                print(f"  [warn] no data for day={day_num} mem={mem_idx}")

        print()

    # ── Write NetCDF ────────────────────────────────────────────────────────────
    print(f"\nWriting {out_path} …")
    nc = Dataset(out_path, "w", format="NETCDF4")

    # Dimensions
    nc.createDimension("day",       N_DAYS)
    nc.createDimension("member",    N_MEMBERS)
    nc.createDimension("latitude",  n_lat)
    nc.createDimension("longitude", n_lon)

    # Coordinate variables
    lat_v = nc.createVariable("latitude",  "f4", ("latitude",))
    lat_v.units     = "degrees_north"
    lat_v.long_name = "latitude"
    lat_v[:]        = out_lats

    lon_v = nc.createVariable("longitude", "f4", ("longitude",))
    lon_v.units     = "degrees_east"
    lon_v.long_name = "longitude"
    lon_v[:]        = out_lons

    # HDWI
    hdw_v = nc.createVariable("HDWI", "f4", ("day", "member", "latitude", "longitude"),
                               fill_value=np.float32(np.inf))
    hdw_v.units     = "HDW"
    hdw_v.long_name = "Hot-Dry-Windy Index"
    hdw_v[:]        = hdwi_out

    # U (max wind speed)
    u_v = nc.createVariable("U", "f4", ("day", "member", "latitude", "longitude"))
    u_v.units     = "m/s"
    u_v.long_name = "Maximum Wind Speed"
    u_v[:]        = u_out

    # VPD
    vpd_v = nc.createVariable("VPD", "f4", ("day", "member", "latitude", "longitude"))
    vpd_v.units     = "hPa"
    vpd_v.long_name = "Maximum Vapor Pressure Deficit"
    vpd_v[:]        = vpd_out

    # Global attributes (mirror the sample file)
    nc.run_date = run_date.strftime("%Y%m%d")
    nc.created  = dt.datetime.utcnow().isoformat()

    nc.close()
    print(f"Done → {out_path}")


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch GEFS data and compute HDWI NetCDF."
    )
    parser.add_argument(
        "--date", default=None,
        help="GEFS run date YYYYMMDD (default: today)"
    )
    parser.add_argument(
        "--out", default="GEFS_HDW_FCST.nc",
        help="Output NetCDF path (default: GEFS_HDW_FCST.nc)"
    )
    parser.add_argument(
        "--cache", default="./gefs_cache",
        help="Directory to cache downloaded GRIB2 files (default: ./gefs_cache)"
    )
    args = parser.parse_args()

    if args.date:
        run_date = dt.datetime.strptime(args.date, "%Y%m%d").date()
    else:
        run_date = dt.date.today()

    print(f"GEFS run date : {run_date.strftime('%Y-%m-%d')} 00z")
    print(f"Output file   : {args.out}")
    print(f"Cache dir     : {args.cache}")
    print(f"Using xarray/cfgrib: {USE_XARRAY}")

    build_gefs_hdw_nc(run_date, args.out, args.cache)