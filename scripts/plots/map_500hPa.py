#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import os, cfgrib
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
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
EVENT_TAG = os.environ.get("EVENT_TAG", "202507_20250718_20250722")
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
OUTFILE = FIG_DIR / "plot_field_500_era5_grib.png"



# =========================
# I/O
# =========================
FIG_DIR = FIG_ROOT / "era5"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# CONFIG
# =========================



TIDX   = int(os.environ.get("TIDX", "0"))  # índice temporal

def get_extent_from_env():
    try:
        return (float(os.environ["LON_W"]), float(os.environ["LON_E"]),
                float(os.environ["LAT_S"]), float(os.environ["LAT_N"]))
    except Exception:
        return None
EXTENT = get_extent_from_env()

# =========================
# Paleta de T (misma idea que 700 hPa, sin grises)
# =========================
# Niveles para colorear contornos (no sombreado): -50 a +5 cada 5
temp_bounds = [-50,-45,-40,-35,-30,-25,-20,-15,-10,-5,0,5]
temp_colors = [
    "#7a1f7a","#a02aa0",                      # violetas
    "#2530cc","#3358ff","#3c8cff","#44b6ff",  # azules
    "#40e0ff","#18c8c8",                      # cian
    "#00a833","#00cc33",                      # verdes
    "#ffee33","#ffcc00"                       # amarillo → naranja claro (0 y +5)
]
cmap_t = mcolors.ListedColormap(temp_colors, name="t500_contours")
norm_t = mcolors.BoundaryNorm(temp_bounds, cmap_t.N, extend="neither")

# =========================
# Carga
# =========================
ds = xr.open_dataset(PLEV_GRIB, engine="cfgrib")
lev = "isobaricInhPa" if "isobaricInhPa" in ds.dims else "level"

# Temperatura 500 hPa [°C]
T500 = ds["t"].sel({lev: 500}).isel(time=TIDX) - 273.15
# Geopotencial 500 hPa → altura geométrica [dam]
g0 = 9.80665
Z500_dam = (ds["z"].sel({lev: 500}).isel(time=TIDX) / g0) / 10.0  # dam

lons = Z500_dam["longitude"].values
lats = Z500_dam["latitude"].values

# =========================
# Niveles de contorno
# =========================
# Isotermas cada 5°C entre –50 y +5
iso_T_levels = np.arange(-50, 6, 5)

# Z500 cada 6 dam entre 490 y 594, con 552 resaltada
z_levels_all = np.arange(490, 595, 6)
z_level_fat  = 552

# =========================
# Figura
# =========================
fig = plt.figure(figsize=(9.6, 7.2), dpi=150)
ax = plt.axes(projection=ccrs.PlateCarree())
if EXTENT:
    ax.set_extent(EXTENT, crs=ccrs.PlateCarree())

# Base cartográfica con colores como la muestra
ax.add_feature(cfeature.LAND, facecolor="#ccff99", zorder=0)   # verde pasto suave
ax.add_feature(cfeature.OCEAN, facecolor="#eeeeee", zorder=0)  # gris clarito
ax.add_feature(cfeature.COASTLINE, edgecolor="#666666", linewidth=0.6)
ax.add_feature(cfeature.BORDERS,   edgecolor="#666666", linewidth=0.4)

# --- Contornos Z500 (negro, más gruesos) ---
cs_z = ax.contour(lons, lats, Z500_dam, levels=z_levels_all,
                  colors="k", linewidths=1.2, transform=ccrs.PlateCarree())
ax.clabel(cs_z, inline=True, fontsize=8, fmt="%d")

# Línea 552 dam aún más gruesa
if z_level_fat in z_levels_all:
    ax.contour(lons, lats, Z500_dam, levels=[z_level_fat],
               colors="k", linewidths=2.2, transform=ccrs.PlateCarree())

# --- Isotermas (discontinuas, más gruesas, coloreadas con cmap) ---
cs_t = ax.contour(lons, lats, T500, levels=iso_T_levels,
                  cmap=cmap_t, norm=norm_t,
                  linewidths=1.6, linestyles="--",
                  transform=ccrs.PlateCarree())

# Etiquetas de temperatura: más grandes, negrita y con halo blanco
labels = ax.clabel(cs_t, inline=True, fontsize=11, fmt=lambda v: f"{int(np.round(v))}°",
                   inline_spacing=3)
for txt in labels:
    txt.set_fontweight("bold")
    txt.set_path_effects([pe.Stroke(linewidth=2.0, foreground="white"), pe.Normal()])

# --- Título ---
valid_time = np.datetime_as_string(Z500_dam.time.values, unit='h')
ax.set_title(
    f"Z 500 hPa (negro, 6 dam; 552 resaltada)  +  Isotermas 500 hPa (discontinuas, 5°C, color)\n{valid_time} UTC",
    fontsize=11
)

plt.tight_layout()
plt.savefig(OUTFILE, bbox_inches="tight")
print(f"[OK] Figura guardada en: {OUTFILE}")

