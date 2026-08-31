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
OUTFILE = os.path.join(FIGDIR, "plot_300hPa_Z_wind.png")

# =========================
# CONFIG
# =========================
DIRDATA   = str(Path(__file__).resolve().parents[2] / "data") + "/events_small_dense/202507/202507_20250718_20250722"
PLEV_GRIB = f"{DIRDATA}/eventsS_pressure_202507_20250718_20250722.grib"

TIDX   = int(os.environ.get("TIDX", "0"))      # índice temporal
LABEL_STEP_DEG = float(os.environ.get("LABEL_STEP_DEG", "2.0"))  # raleo de etiquetas de viento (si se quisieran)
def get_extent_from_env():
    try:
        return (float(os.environ["LON_W"]), float(os.environ["LON_E"]),
                float(os.environ["LAT_S"]), float(os.environ["LAT_N"]))
    except Exception:
        return None
EXTENT = get_extent_from_env()

# =========================
# Paleta de viento (kt) para sombreado
# 60 80 100 120 140 160 180  (under -> transparente)
# Colores aproximados a la barra: verde muy claro -> verde fuerte -> amarillo -> naranjas -> rojos
# =========================
wind_bounds = np.array([60, 80, 100, 120, 140, 160, 180])
wind_colors = [
    "#bfffd0",  # 60-80  (verde muy claro)
    "#66ff7a",  # 80-100 (verde)
    "#00cc00",  # 100-120 (verde fuerte)
    "#ffeb66",  # 120-140 (amarillo)
    "#ffb347",  # 140-160 (naranja)
    "#ff6f61",  # 160-180 (naranja-rojizo)
    "#e00000",  # >=180   (rojo)
]
cmap_w = mcolors.ListedColormap(wind_colors, name="wind300_custom")
# extend='max' porque el under (<60) lo enmascaramos -> transparente
norm_w = mcolors.BoundaryNorm(wind_bounds, cmap_w.N, extend="max")
cmap_w.set_bad(alpha=0.0)  # enmascarados (NaN) transparentes

# =========================
# Carga
# =========================
ds = xr.open_dataset(PLEV_GRIB, engine="cfgrib")
lev = "isobaricInhPa" if "isobaricInhPa" in ds.dims else "level"

# Z300: ERA5 'z' es geopotential [m^2/s^2]; altura geométrica = z/g [m]
g0 = 9.80665
Z300_dam = (ds["z"].sel({lev: 300}).isel(time=TIDX) / g0) / 10.0  # [dam]

# Viento 300 hPa (nudos)
U300 = ds["u"].sel({lev: 300}).isel(time=TIDX)
V300 = ds["v"].sel({lev: 300}).isel(time=TIDX)
WSPD = np.hypot(U300, V300) * 1.943844  # m/s -> kt

# Enmascarar < 60 kt (no sombrear)
WSPD_masked = WSPD.where(WSPD >= wind_bounds[0])

lons = Z300_dam["longitude"].values
lats = Z300_dam["latitude"].values

# =========================
# Contornos Z300 cada 16 dam, alineados cerca de 912
# =========================
zmin = float(np.nanmin(Z300_dam))
zmax = float(np.nanmax(Z300_dam))
base = 16.0
# centramos cerca de 912 (ajusta para anclar la parrilla)
offset = 912.0 % base  # 0 si ya está alineado
start = np.floor((zmin - offset) / base) * base + offset
stop  = np.ceil ((zmax - offset) / base) * base + offset
z_levels = np.arange(start, stop + 0.1, base)

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

# Sombreado de viento (>=60 kt)
mesh = ax.pcolormesh(lons, lats, WSPD_masked, cmap=cmap_w, norm=norm_w, shading="auto")

# Contornos negros de Z300 (dam) cada 16
cs = ax.contour(Z300_dam["longitude"], Z300_dam["latitude"], Z300_dam,
                levels=z_levels, colors="k", linewidths=0.7, transform=ccrs.PlateCarree())
ax.clabel(cs, inline=True, fontsize=7, fmt="%d")


# =========================
# Escala textual de viento (compacta, sin barra)
# =========================
scale_vals = [60, 80, 100, 120, 140, 160, 180]
x0, x1 = 0.02, 0.4   # arranca en 0.05 y ocupa poco ancho
y  = -0.055           # posición vertical (debajo del eje)
xs = np.linspace(x0, x1, len(scale_vals))

for xv, sv in zip(xs, scale_vals):
    ax.text(xv, y, f"{sv}", transform=ax.transAxes,
            ha="center", va="center", fontsize=11,
            color=cmap_w(norm_w(sv)))

# Título
valid_time = np.datetime_as_string(Z300_dam.time.values, unit='h')
ax.set_title(f"Z 300 hPa (cont. negros cada 16 dam)  +  Viento 300 hPa (sombreado ≥ 60 kt)\n{valid_time} UTC",
             fontsize=11)

plt.tight_layout()
plt.savefig(OUTFILE, bbox_inches="tight")
print(f"[OK] Figura guardada en: {OUTFILE}")
