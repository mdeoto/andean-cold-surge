#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import os, cfgrib
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature


# =========================
# I/O
# =========================
FIGDIR  = '/home/mdeoto/investigacion/mountain_ridge/figs/era5'
os.makedirs(FIGDIR, exist_ok=True)
OUTFILE = os.path.join(FIGDIR, "plot_field_700_era5_grib.png")

# =========================
# CONFIG
# =========================
DIRDATA   = str(Path(__file__).resolve().parents[2] / "data") + "/events_small_dense/202507/202507_20250718_20250722"
PLEV_GRIB = f"{DIRDATA}/eventsS_pressure_202507_20250718_20250722.grib"

TIDX   = int(os.environ.get("TIDX", "0"))      # índice temporal
LABEL_STEP_DEG = float(os.environ.get("LABEL_STEP_DEG", "1.0"))  # raleo numérico de T
# Extensión opcional
def get_extent_from_env():
    try:
        return (float(os.environ["LON_W"]), float(os.environ["LON_E"]),
                float(os.environ["LAT_S"]), float(os.environ["LAT_N"]))
    except Exception:
        return None
EXTENT = get_extent_from_env()

# =========================
# Paleta de T (discreta, 2°C)
# (similar a la operativa que usaste)
# =========================
# Bordes de clase (°C): más finos entre -12 y +14, más gruesos fuera
temp_bounds = [-54, -48, -42, -36, -30, -24, -18, -12, -8, -6, -4, -2, 0, 2, 4, 6, 8, 12, 18, 24, 30, 36, 42, 48, 54]

# Colores por tramo (len = len(temp_bounds)-1)
temp_colors = [
    # Underflow
    "#4c4c4c",  
    # 26 tramos reales
    "#5c5c5c","#6d6d6d","#818181","#9a9a9a","#b3b3b3",   # grises
    "#7a1f7a","#a02aa0",                                 # violetas
    "#2530cc","#3358ff","#3c8cff","#44b6ff",             # azules
    "#40e0ff","#18c8c8",                                 # cian
    "#00a833","#00cc33",                                 # verdes
    "#d4ff33","#ffee33",                                 # amarillos
    "#ffcc00",                                           # naranja-amarillo
    "#ff9900","#ff7a00","#ff4d4d","#e00000","#b00000","#8a0000",  # naranjas-rojos
    # Overflow
    "#8a0000"
]

cmap_t = mcolors.ListedColormap(temp_colors, name="t700_custom")
norm_t = mcolors.BoundaryNorm(temp_bounds, cmap_t.N, extend="both")

# =========================
# Carga
# =========================
ds = xr.open_dataset(PLEV_GRIB, engine="cfgrib")
lev = "isobaricInhPa" if "isobaricInhPa" in ds.dims else "level"

# T700 [°C]
T700 = ds["t"].sel({lev: 700}).isel(time=TIDX) - 273.15
# Z700: ERA5 'z' es geopotential [m^2/s^2]; altura geométrica = z/g [m]
g0 = 9.80665
H700_dam = (ds["z"].sel({lev: 700}).isel(time=TIDX) / g0) / 10.0  # dam

lons = T700["longitude"].values
lats = T700["latitude"].values

# =========================
# Contornos Z700 cada 16 dam
# =========================
zmin = float(np.nanmin(H700_dam))
zmax = float(np.nanmax(H700_dam))
# llevar a múltiplos de 16
base = 16.0
z0 = np.floor(zmin / base) * base
z1 = np.ceil (zmax / base) * base
z_levels = np.arange(z0, z1 + 0.1, base)

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

# Sombreado de T700
mesh = ax.pcolormesh(lons, lats, T700, cmap=cmap_t, norm=norm_t, shading="auto")

# Contornos negros de Z700 (dam) cada 16
cs = ax.contour(H700_dam["longitude"], H700_dam["latitude"], H700_dam,
                levels=z_levels, colors="k", linewidths=0.7, transform=ccrs.PlateCarree())
ax.clabel(cs, inline=True, fontsize=7, fmt="%d")

# Números de T en la grilla (raleados)
dy = abs(float(lats[1] - lats[0])); dx = abs(float(lons[1] - lons[0]))
i_stride = max(1, int(round(LABEL_STEP_DEG / dy)))
j_stride = max(1, int(round(LABEL_STEP_DEG / dx)))
LATv = lats[::i_stride]
LONv = lons[::j_stride]
Tval = T700.values[::i_stride, ::j_stride]
for i, lat in enumerate(LATv):
    for j, lon in enumerate(LONv):
        val = Tval[i, j]
        if np.isfinite(val):
            ax.text(lon, lat, f"{int(np.round(val))}",
                    ha='center', va='center', fontsize=6.5, color='k',
                    transform=ccrs.PlateCarree())

# Colorbar y título
cbar = plt.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.03, fraction=0.05, extend="both")
cbar.set_label("Temp. 700 hPa (°C)")

# Ticks “densos” como en la imagen (podés aligerar si queda muy cargado)
cbar.set_ticks(temp_bounds)
valid_time = np.datetime_as_string(T700.time.values, unit='h')
ax.set_title(f"Geopot. 700 hPa (dam) – contornos cada 16  •  Temp. 700 hPa (sombreado)  •  {valid_time} UTC",
             fontsize=11)

plt.tight_layout()
plt.savefig(OUTFILE, bbox_inches="tight")
print(f"[OK] Figura guardada en: {OUTFILE}")
