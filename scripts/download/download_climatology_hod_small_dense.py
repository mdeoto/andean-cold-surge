#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, time
from pathlib import Path
import cdsapi

# ===== CONFIG =====
PROJECT_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = Path(
    os.environ.get("COLD_SURGE_BASEDIR", PROJECT_DIR / "data")
).resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)

AREA_SMALL = [-30, -75, -45, -60]  # [N, W, S, E]
CLIM_YEARS = list(range(1991, 2021))
HOURS24 = [f"{h:02d}:00" for h in range(24)]

# niveles densos: 1000→500 cada ~25 hPa + 300/250
HOD_PLEVS_DENSE = [
 '1000','975','950','925','900','875','850','825','800','775','750',
 '725','700','675','650','625','600','575','550','525','500','300','250'
]

# para estabilidad del endpoint en HOD small, limitar a 4 vars clave
HOD_PLEV_VARS_DENSE = [
    'geopotential','temperature','u_component_of_wind','v_component_of_wind',
    'specific_humidity','vertical_velocity'
]

HOD_SFC_VARS  = [
    '10m_u_component_of_wind','10m_v_component_of_wind','2m_temperature',
    'land_sea_mask','mean_sea_level_pressure','sea_surface_temperature',
    'low_cloud_cover','snowfall','total_precipitation','sea_ice_cover',
]


def months_from_env_or_events():
    env = os.environ.get("MONTHS", "").strip()
    if env:
        return sorted({int(m) for m in env.split(",") if m})
    months = set()
    for root_sub in ["events_small_dense"]:
        root = BASE_DIR / root_sub
        if not root.exists(): continue
        for d in root.iterdir():
            if d.is_dir() and len(d.name)==6 and d.name.isdigit():
                months.add(int(d.name[-2:]))
    # si no detecta, caer al 7 (ejemplo)
    return sorted(months) or [7]


def yearly_dir_for_month(m, kind="small_dense"):
    d = BASE_DIR / f"climatology_{kind}" / f"{int(m):02d}" / "yearly_hod"
    d.mkdir(parents=True, exist_ok=True)
    return d

def retrieve_hod_month(c, year, month, area, outp_p, outp_s):
    req_hp = {
        "product_type":"monthly_averaged_reanalysis_by_hour_of_day",
        "format":"grib",
        "variable": HOD_PLEV_VARS_DENSE,
        "pressure_level": HOD_PLEVS_DENSE,
        "year": str(year),
        "month": f"{int(month):02d}",
        "time": HOURS24,
        "area": area,
    }
    req_hs = {
        "product_type":"monthly_averaged_reanalysis_by_hour_of_day",
        "format":"grib",
        "variable": HOD_SFC_VARS,
        "year": str(year),
        "month": f"{int(month):02d}",
        "time": HOURS24,
        "area": area,
    }
    c.retrieve("reanalysis-era5-pressure-levels-monthly-means", req_hp, str(outp_p))
    c.retrieve("reanalysis-era5-single-levels-monthly-means",  req_hs, str(outp_s))

def main():
    months = months_from_env_or_events()
    print(f"[CLIM-S] Meses HOD: {months}")
    c = cdsapi.Client()
    for m in months:
        ydir = yearly_dir_for_month(m, "small_dense")
        for y in CLIM_YEARS:
            outp = ydir / f"clim_pressure_hod_{y}{m:02d}.nc"
            outs = ydir / f"clim_surface_hod_{y}{m:02d}.nc"
            if outp.exists() and outs.exists(): continue
            tries = 0
            while True:
                tries += 1
                try:
                    print(f"[HOD-S] {y}-{m:02d}")
                    retrieve_hod_month(c, y, m, AREA_SMALL, outp, outs)
                    break
                except Exception as e:
                    print(f"[WARN] {y}-{m:02d} intento {tries} falló: {e}")
                    if tries >= 3: raise
                    time.sleep(10)
    print("[DONE] HOD small-dense 1991–2020.")

if __name__ == "__main__":
    main()

