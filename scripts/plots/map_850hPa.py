#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import os
import numpy as np
import xarray as xr
import cfgrib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# =========================
# PROJECT PATHS
# =========================
PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("COLD_SURGE_BASEDIR", PROJECT_DIR / "data")).resolve()
FIG_ROOT = Path(os.environ.get("COLD_SURGE_FIGDIR", PROJECT_DIR / "figs")).resolve()

# =========================
# EVENT CONFIGURATION
# =========================
EVENT_TAG = os.environ.get("EVENT_TAG", "202307_20230715_20230719")
EVENT_MONTH = EVENT_TAG.split("_")[0]

EVENT_DIR = (
    DATA_DIR
    / "events_small_dense"
    / EVENT_MONTH
    / EVENT_TAG
)

PLEV_GRIB = EVENT_DIR / f"eventsS_pressure_{EVENT_TAG}.grib"
SFC_GRIB = EVENT_DIR / f"eventsS_surface_{EVENT_TAG}.grib"

FIG_DIR = FIG_ROOT / "era5"
FIG_DIR.mkdir(parents=True, exist_ok=True)
OUTFILE = FIG_DIR / "plot_field_850_era5_grib.png"



# =========================
# I/O
# =========================
FIG_DIR = FIG_ROOT / "era5"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# CONFIG
# =========================




# Extensión opcional del mapa (ENV). Si no está, usa todo el dominio del GRIB
def get_extent_from_env():
    try:
        return (
            float(os.environ["LON_W"]),
            float(os.environ["LON_E"]),
            float(os.environ["LAT_S"]),
            float(os.environ["LAT_N"]),
        )
    except Exception:
        return None

EXTENT = get_extent_from_env()

# Índice temporal a graficar
TIDX = int(os.environ.get("TIDX", "0"))

# ======================================================
# PALETA EXACTA (cada 2 °C) QUE PASASTE
# ======================================================
temp_values = np.array([
    -28,-26,-24,-22,-20,-18,-16,-14,-12,-10,-8,-6,-4,-2, 0, 2, 4, 6, 8,10,
     12, 14, 16, 18, 20, 22, 24, 26,28,30,32,34,36,38,40,42,44,46,48
])
temp_colors = [
    "#666666","#888888","#b0b0b0","#cccccc","#e4e4e4","#773377","#aa33aa","#cc33cc",
    "#ff33ff","#ff99ff","#1500cc","#3366ff","#3399ff","#33ccff","#33ffff","#007700",
    "#009900","#00bb00","#00dd00","#00ff00","#ffff33","#ffee33","#ffdd33","#ffcc33",
    "#ffbb33","#ffaa00","#ff9900","#ff7700","#ff0000","#ee0000","#cc0000","#bb0000",
    "#aa0000","#990000","#880000","#720000","#5b0000","#420000","#1d0000"
]
cmap_temp = mcolors.ListedColormap(temp_colors)
norm_temp = mcolors.BoundaryNorm(temp_values, cmap_temp.N + 1, extend="both")

# ======================================================
# LOADERS
# ======================================================
def load_pressure(path):
    """Abre el GRIB de niveles de presión (cfgrib)"""
    return xr.open_dataset(path, engine="cfgrib")

def load_surface(path):
    """Abre el GRIB de superficie con múltiples grupos y devuelve el grupo instantáneo (msl, t2m, u10, v10, etc.)."""
    groups = cfgrib.open_datasets(path, indexpath="")
    inst = [ds for ds in groups if "step" not in ds.dims]
    if not inst:
        raise RuntimeError("No se encontró grupo instantáneo en el GRIB de superficie.")
    return inst[0]

# ======================================================
# MAIN
# ======================================================
def main():
    ds_p = load_pressure(PLEV_GRIB)
    ds_s = load_surface(SFC_GRIB)

    level_coord = "isobaricInhPa" if "isobaricInhPa" in ds_p.dims else "level"
    # T850 a °C, U/V opcionales (no se grafican)
    t850 = ds_p["t"].sel({level_coord: 850}) - 273.15

    # SLP a hPa
    msl = ds_s["msl"] / 100.0

    # seleccionar tiempo
    t850_t = t850.isel(time=TIDX)
    msl_t  = msl.isel(time=TIDX)
    valid_time = np.datetime_as_string(t850_t.time.values, unit="h")

    # lon/lat
    lons = t850_t["longitude"]
    lats = t850_t["latitude"]

    # ================== FIGURA ==================
    fig = plt.figure(figsize=(8, 10), dpi=150)
    ax = plt.axes(projection=ccrs.PlateCarree())

    if EXTENT:
        ax.set_extent(EXTENT, crs=ccrs.PlateCarree())

    # base cartográfica
    ax.add_feature(cfeature.LAND, facecolor="tan", alpha=0.5, zorder=0)
    ax.add_feature(cfeature.OCEAN, facecolor="lightblue", alpha=0.5, zorder=0)
    ax.add_feature(cfeature.COASTLINE, edgecolor="gray", linewidth=0.5)
    ax.add_feature(cfeature.BORDERS,   edgecolor="gray", linewidth=0.5)

    # sombreado T850
    mesh = ax.pcolormesh(lons, lats, t850_t, cmap=cmap_temp, norm=norm_temp, shading="auto")

    # SLP cada 2 hPa fijo 980–1040; colores por tramo
    slp_levels = np.arange(980, 1040 + 0.1, 2)
    slp_colors = ["blue" if lvl <= 1012 else "red" if lvl >= 1014 else "black" for lvl in slp_levels]
    cs = ax.contour(msl_t["longitude"], msl_t["latitude"], msl_t,
                    levels=slp_levels, colors=slp_colors, linewidths=0.6, transform=ccrs.PlateCarree())
    ax.clabel(cs, inline=True, fontsize=7, fmt="%d hPa")

    # Etiquetas numéricas raleadas de T850 (~1.25° por defecto, ajustable por env LABEL_STEP_DEG)
    label_step_deg = float(os.environ.get("LABEL_STEP_DEG", "1.25"))
    dy = abs(float(lats[1] - lats[0])); dx = abs(float(lons[1] - lons[0]))
    i_stride = max(1, int(round(label_step_deg / dy)))
    j_stride = max(1, int(round(label_step_deg / dx)))
    LATv = lats.values[::i_stride]
    LONv = lons.values[::j_stride]
    Tval = t850_t.values[::i_stride, ::j_stride]
    for i, lat in enumerate(LATv):
        for j, lon in enumerate(LONv):
            val = Tval[i, j]
            if np.isfinite(val):
                ax.text(lon, lat, f"{int(np.round(val))}", ha="center", va="center",
                        fontsize=5.5, color="k", transform=ccrs.PlateCarree())

    # colorbar + títulos
    cbar = plt.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.02, shrink=0.70, extend="both")
    cbar.set_label("Temperatura 850 hPa (°C)")
    cbar.set_ticks([-28, -20, -10, 0, 10, 26, 38, 48])
    cbar.set_ticklabels([-28, -20, -10, 0, 10, 26, 38, 48])

    ax.set_title(f"SLP / Temp. 850 hPa • {valid_time} UTC", loc="left", fontsize=12)
    ax.set_title("ERA5", loc="right", fontsize=12)

    plt.tight_layout()
    plt.savefig(OUTFILE, bbox_inches="tight")
    print(f"[OK] Figura guardada en: {OUTFILE}")

if __name__ == "__main__":
    main()
