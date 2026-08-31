#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from datetime import datetime, timedelta
import cdsapi

# ========= CONFIG =========
PROJECT_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = Path(
    os.environ.get("COLD_SURGE_BASEDIR", PROJECT_DIR / "data")
).resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)

# Dominio chico (zona cordillera norte Patagonia)
AREA_SMALL = [-30, -75, -45, -60]   # [N, W, S, E]
PAD_DAYS   = int(os.environ.get("PAD_DAYS", "2"))
HOURS3     = [f"{h:02d}:00" for h in range(0, 24, 3)]

EVENT_DAYS0 = os.environ.get("EVENT_DAYS0").split(",")

# Niveles densos 1000→500 cada ~25 hPa + 300/250
PLEVS_EVT_DENSE = [
 '1000','975','950','925','900','875','850','825','800','775','750',
 '725','700','675','650','625','600','575','550','525','500','300','250'
]
PLEV_VARS_EVT = [
    'geopotential','temperature','u_component_of_wind','v_component_of_wind',
    'specific_humidity','vertical_velocity'
]
SFC_VARS_EVT = [
    '10m_u_component_of_wind','10m_v_component_of_wind','2m_temperature',
    'land_sea_mask','mean_sea_level_pressure','sea_surface_temperature',
    'low_cloud_cover','snowfall','total_precipitation','sea_ice_cover',
]

def make_windows(days0, pad_days=2):
    evts = []
    for d0_str in days0:
        d0 = datetime.fromisoformat(d0_str.strip())
        evts.append(((d0-timedelta(days=pad_days)).strftime("%Y-%m-%d"),
                     (d0+timedelta(days=pad_days)).strftime("%Y-%m-%d")))
    return evts

def days_list(start, end):
    d0 = datetime.fromisoformat(start); d1 = datetime.fromisoformat(end)
    out, d = [], d0
    while d <= d1:
        out.append(d.strftime("%d")); d += timedelta(days=1)
    return out

def yyyymm(start):
    s = datetime.fromisoformat(start); return s.strftime("%Y%m"), s.strftime("%Y"), s.strftime("%m")

def tag_range(start, end):
    yyyymm_, y, m = yyyymm(start); return f"{y}{m}_{start.replace('-','')}_{end.replace('-','')}"

def retrieve_event_month(c, year, month, days, hours, area, outp, outs):
    c.retrieve("reanalysis-era5-pressure-levels", {
        "product_type": "reanalysis", "format": "grib",
        "variable": PLEV_VARS_EVT, "pressure_level": PLEVS_EVT_DENSE,
        "year": year, "month": month, "day": days, "time": hours, "area": area
    }, str(outp))
    c.retrieve("reanalysis-era5-single-levels", {
        "product_type": "reanalysis", "format": "grib",
        "variable": SFC_VARS_EVT, "year": year, "month": month, "day": days,
        "time": hours, "area": area
    }, str(outs))

def main():
    print(f"[BASE] {BASE_DIR}")
    c = cdsapi.Client()
    for (start, end) in make_windows(EVENT_DAYS0, PAD_DAYS):
        yyyymm_, y, m = yyyymm(start)
        tag = tag_range(start, end)
        evdir = BASE_DIR / "events_small_dense" / yyyymm_ / tag
        evdir.mkdir(parents=True, exist_ok=True)
        outp = evdir / f"eventsS_pressure_{tag}.grib"
        outs = evdir / f"eventsS_surface_{tag}.grib"
        if outp.exists() and outs.exists():
            print(f"[SKIP] {tag} (ya existe)"); continue
        print(f"[EVENT-S] {start}→{end}")
        retrieve_event_month(c, y, m, days_list(start, end), HOURS3, AREA_SMALL, outp, outs)

if __name__ == "__main__":
    main()

