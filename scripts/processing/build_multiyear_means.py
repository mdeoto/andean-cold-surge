#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from pathlib import Path
import xarray as xr

PROJECT_DIR = Path(__file__).resolve().parents[2]
BASE_DIR = Path(
    os.environ.get("COLD_SURGE_BASEDIR", PROJECT_DIR / "data")
).resolve()

CLIM_KINDS = ["climatology_large", "climatology_small_dense"]
CLIM_YEARS = list(range(1991, 2021))

def months_from_env_or_dirs(kind_dir: Path):
    env = os.environ.get("MONTHS", "").strip()
    if env:
        return sorted({int(m) for m in env.split(",") if m})
    months = []
    if kind_dir.exists():
        for d in sorted(p for p in kind_dir.iterdir() if p.is_dir() and p.name.isdigit()):
            months.append(int(d.name))
    if not months:
        raise RuntimeError("No hay meses en $MONTHS ni carpetas en climatology_*.")
    return sorted(months)

def build_for_kind(kind):
    base = BASE_DIR / kind
    months = months_from_env_or_dirs(base)
    print(f"[MULTI] {kind} meses={months}")
    for m in months:
        month_dir = base / f"{m:02d}"
        yearly_dir = month_dir / "yearly_hod"
        multi_dir  = month_dir / "multi"
        multi_dir.mkdir(parents=True, exist_ok=True)

        pres_files = [yearly_dir / f"clim_pressure_hod_{y}{m:02d}.nc" for y in CLIM_YEARS]
        sfc_files  = [yearly_dir / f"clim_surface_hod_{y}{m:02d}.nc"  for y in CLIM_YEARS]

        # sanity (mínimo: que existan todos)
        missing = [str(fp) for fp in pres_files + sfc_files if not fp.exists()]
        if missing:
            print(f"[WARN] Faltan archivos HOD en {kind} {m:02d}. Ejemplos:\n  " + "\n  ".join(missing[:5]))
            print("      (salto este mes para este kind)")
            continue

        ds_p = xr.concat([xr.open_dataset(fp) for fp in pres_files],
                         dim="year").assign_coords(year=("year", CLIM_YEARS))
        ds_s = xr.concat([xr.open_dataset(fs) for fs in sfc_files],
                         dim="year").assign_coords(year=("year", CLIM_YEARS))

        clim_p = ds_p.mean(dim="year", keep_attrs=True)
        clim_s = ds_s.mean(dim="year", keep_attrs=True)

        outp = multi_dir / f"CLIM_multi_{m:02d}_pressure_hod.nc"
        outs = multi_dir / f"CLIM_multi_{m:02d}_surface_hod.nc"
        clim_p.to_netcdf(outp)
        clim_s.to_netcdf(outs)
        print(f"[OK] {kind} {m:02d} → {outp.name}, {outs.name}")

def main():
    for kind in CLIM_KINDS:
        build_for_kind(kind)
    print("[DONE] Multi-años generados.")

if __name__ == "__main__":
    main()
