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

AREA_BIG = [-15, -100, -65, -30]  # [N, W, S, E]
CLIM_YEARS = list(range(1991, 2021))
HOURS24 = [f"{h:02d}:00" for h in range(24)]

# niveles/vars "seguras" para HOD en dominio grande
HOD_PLEVS = ['1000','925','850','700','500','250']

HOD_PLEV_VARS = [
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
    # buscamos en ambas raíces
    for root_sub in ["events_large"]:
        root = BASE_DIR / root_sub
        if not root.exists():
            continue
        for d in root.iterdir():
            if d.is_dir() and len(d.name) == 6 and d.name.isdigit():
                months.add(int(d.name[-2:]))
    if not months:
        raise RuntimeError(
            "❌ No se detectaron meses ni en $MONTHS ni en eventos previos (large/small_dense)."
        )
    return sorted(months)

def yearly_dir_for_month(m, kind="large"):
    d = BASE_DIR / f"climatology_{kind}" / f"{int(m):02d}" / "yearly_hod"
    d.mkdir(parents=True, exist_ok=True)
    return d

def retrieve_hod_month(c, year, month, area, outp_p, outp_s):
    req_hp = {
        "product_type":"monthly_averaged_reanalysis_by_hour_of_day",
        "format":"grib",
        "variable": HOD_PLEV_VARS,
        "pressure_level": HOD_PLEVS,
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
    print(f"[CLIM-L] Meses HOD: {months}")
    c = cdsapi.Client()
    for m in months:
        ydir = yearly_dir_for_month(m, "large")
        for y in CLIM_YEARS:
            outp = ydir / f"clim_pressure_hod_{y}{m:02d}.nc"
            outs = ydir / f"clim_surface_hod_{y}{m:02d}.nc"
            if outp.exists() and outs.exists(): continue
            tries = 0
            while True:
                tries += 1
                try:
                    print(f"[HOD-L] {y}-{m:02d}")
                    retrieve_hod_month(c, y, m, AREA_BIG, outp, outs)
                    break
                except Exception as e:
                    print(f"[WARN] {y}-{m:02d} intento {tries} falló: {e}")
                    if tries >= 3: raise
                    time.sleep(10)
    print("[DONE] HOD large 1991–2020.")

if __name__ == "__main__":
    main()

