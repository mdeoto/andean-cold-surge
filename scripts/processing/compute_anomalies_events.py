#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from pathlib import Path
import pandas as pd
import xarray as xr
import cfgrib

PROJECT_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = Path(
    os.environ.get("COLD_SURGE_BASEDIR", PROJECT_DIR / "data")
).resolve()

KIND_TO_DIR = {
    "events_large":       "climatology_large",
    "events_small_dense": "climatology_small_dense",
}

def months_in_events(root_events: Path):
    months = []
    if root_events.exists():
        for d in sorted(p for p in root_events.iterdir() if p.is_dir() and p.name.isdigit()):
            months.append(int(d.name[-2:]))
    return sorted(set(months))

def match_hour_coord(ds):
    hrs = pd.to_datetime(ds.time.values).hour
    return ds.assign_coords(hour=("time", hrs))

def open_surface_grib(path_grib: Path):
    """cfgrib: single-levels puede venir en grupos; unimos instantáneos (sin 'step')."""
    groups = cfgrib.open_datasets(str(path_grib), indexpath="")
    inst = [ds for ds in groups if 'step' not in ds.dims]
    if not inst:
        # si no hay instantáneos, tomamos el primero
        inst = [groups[0]]
    return xr.merge(inst)

def open_pressure_grib(path_grib: Path):
    return xr.open_dataset(path_grib, engine="cfgrib")

def compute_for_kind(kind_events: str):
    root = BASE_DIR / kind_events
    clim_kind = KIND_TO_DIR[kind_events]
    if not root.exists():
        print(f"[INFO] {root} no existe. Salto.")
        return

    months = months_in_events(root)
    if not months:
        print(f"[INFO] No hay meses en {kind_events}. Salto.")
        return

    for ymm in sorted(p for p in root.iterdir() if p.is_dir() and p.name.isdigit()):
        m = int(ymm.name[-2:])
        multi_dir = BASE_DIR / clim_kind / f"{m:02d}" / "multi"
        clim_p_nc = multi_dir / f"CLIM_multi_{m:02d}_pressure_hod.nc"
        clim_s_nc = multi_dir / f"CLIM_multi_{m:02d}_surface_hod.nc"
        if not (clim_p_nc.exists() and clim_s_nc.exists()):
            print(f"[WARN] Falta multi-año {clim_kind} para mes {m:02d}. Salto {ymm.name}.")
            continue

        # abrir climatologías multi
        cl_p = xr.open_dataset(clim_p_nc)  # dims: (time=24, pressure_level, lat, lon)
        cl_s = xr.open_dataset(clim_s_nc)  # dims: (time=24, lat, lon)

        # reindexar por hora
        cl_p_h = cl_p.assign_coords(hour=("time", pd.to_datetime(cl_p.time.values).hour)).swap_dims({"time":"hour"})
        cl_s_h = cl_s.assign_coords(hour=("time", pd.to_datetime(cl_s.time.values).hour)).swap_dims({"time":"hour"})

        for tagdir in sorted(p for p in ymm.iterdir() if p.is_dir()):
            evp = next(tagdir.glob("*pressure_*.grib"), None)
            evs = next(tagdir.glob("*surface_*.grib"), None)
            if not (evp and evs):
                print(f"[WARN] Faltan GRIB en {tagdir}"); continue

            print(f"[ANOM] {kind_events} :: {tagdir.name}")

            # eventos (GRIB)
            ev_p = open_pressure_grib(evp)
            ev_s = open_surface_grib(evs)

            # añadir 'hour' y alinear hora-del-día
            ev_p_h = match_hour_coord(ev_p)
            ev_s_h = match_hour_coord(ev_s)

            # interp climatologías a la grilla del evento
            cl_p_m = cl_p_h.interp(latitude=ev_p_h.latitude, longitude=ev_p_h.longitude)
            cl_s_m = cl_s_h.interp(latitude=ev_s_h.latitude, longitude=ev_s_h.longitude)

            # renombrar 'z'→'geopotential' si corresponde
            if "z" in ev_p_h.data_vars and "geopotential" in cl_p_m.data_vars:
                ev_p_h = ev_p_h.rename({"z": "geopotential"})

            # intersección de variables
            common_p = [v for v in ev_p_h.data_vars if v in cl_p_m.data_vars]
            common_s = [v for v in ev_s_h.data_vars if v in cl_s_m.data_vars]

            if not common_p and not common_s:
                print(f"[WARN] No hay variables comunes en {tagdir.name}.")
                continue

            # anomalías por hora-del-día
            anom_p = ev_p_h[common_p].groupby("hour") - cl_p_m[common_p] if common_p else None
            anom_s = ev_s_h[common_s].groupby("hour") - cl_s_m[common_s] if common_s else None

            # restaurar 'time' original
            if anom_p is not None:
                anom_p = anom_p.assign_coords(time=ev_p.time).swap_dims({"time":"time"})
            if anom_s is not None:
                anom_s = anom_s.assign_coords(time=ev_s.time).swap_dims({"time":"time"})

            # guardar
            if anom_p is not None:
                outp = str(evp).replace(".grib", "_ANOM.nc")
                anom_p.to_netcdf(outp)
            if anom_s is not None:
                outs = str(evs).replace(".grib", "_ANOM.nc")
                anom_s.to_netcdf(outs)

            print(f"[WRITE] {tagdir.name} listo.")

def main():
    for kind in ["events_large", "events_small_dense"]:
        compute_for_kind(kind)
    print("[DONE] Anomalías generadas.")

if __name__ == "__main__":
    main()
