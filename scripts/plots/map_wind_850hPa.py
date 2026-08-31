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
OUTFILE = FIG_DIR / "plot_field_wind850_era5_grib.png"



FIG_DIR = FIG_ROOT / "era5"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# CONFIG
# =========================



TIDX   = int(os.environ.get("TIDX", "0"))
W_SKIP = int(os.environ.get("W_SKIP", "3"))

def get_extent_from_env():
    try:
        return (float(os.environ["LON_W"]), float(os.environ["LON_E"]),
                float(os.environ["LAT_S"]), float(os.environ["LAT_N"]))
    except Exception:
        return None
EXTENT = get_extent_from_env()

MS2KT  = 1.9438444924406048
KTS_MIN = MS2KT  # NO plotear < 5 kt

# Paleta: <10 kt amarillos
bounds = np.array([5,10,15,20,25,30,35,40,45,50,55,60, 1e9])
colors = [
    "#ffd000",  # 5–10 amarillo vivo
    "#22bb66",  # 10–15
    "#11aa88",  # 15–20
    "#1199aa",  # 20–25
    "#1188cc",  # 25–30
    "#1166ee",  # 30–35
    "#3344ee",  # 35–40
    "#6633cc",  # 40–45
    "#9922aa",  # 45–50
    "#cc1188",  # 50–55
    "#ff1144",  # 55–60
    "#ff1144",  # 60+ overflow
]
cmap = mcolors.ListedColormap(colors)
norm = mcolors.BoundaryNorm(bounds, cmap.N)

# -------- CARGA --------
ds   = xr.open_dataset(PLEV_GRIB, engine="cfgrib")
lev  = "isobaricInhPa" if "isobaricInhPa" in ds.dims else "level"
u850 = ds["u"].sel({lev: 850}).isel(time=TIDX)
v850 = ds["v"].sel({lev: 850}).isel(time=TIDX)

lons = u850["longitude"].values
lats = u850["latitude"].values
U    = u850.values
V    = v850.values
spd_kt = np.hypot(U, V) * MS2KT

# Raleo
ii = slice(None, None, W_SKIP)
jj = slice(None, None, W_SKIP)
LONs = lons[jj]; LATs = lats[ii]
Uq = U[ii, jj]; Vq = V[ii, jj]; SQ = spd_kt[ii, jj]

# Filtro duro: sólo >= KTS_MIN
LON2, LAT2 = np.meshgrid(LONs, LATs)
mask = SQ >= KTS_MIN
x_plot = LON2[mask].ravel()
y_plot = LAT2[mask].ravel()
u_plot = Uq[mask].ravel() * MS2KT  # U en kts
v_plot = Vq[mask].ravel() * MS2KT  # V en kts
c_plot = SQ[mask].ravel()          # color en kts

# -------- PLOT --------
fig = plt.figure(figsize=(9.6, 7.2), dpi=150)
ax = plt.axes(projection=ccrs.PlateCarree())
if EXTENT:
    ax.set_extent(EXTENT, crs=ccrs.PlateCarree())

# Base cartográfica con colores como la muestra
ax.add_feature(cfeature.LAND, facecolor="#ccff99", zorder=0)   # verde pasto suave
ax.add_feature(cfeature.OCEAN, facecolor="#eeeeee", zorder=0)  # gris clarito
ax.add_feature(cfeature.COASTLINE, edgecolor="#666666", linewidth=0.6)
ax.add_feature(cfeature.BORDERS,   edgecolor="#666666", linewidth=0.4)

# Barbas invertidas (HS), finas, sin círculo de calma
ax.barbs(
    x_plot, y_plot, u_plot, v_plot, c_plot,
    cmap=cmap, norm=norm,
    flip_barb=True, pivot="middle",
    length=4.2, linewidth=0.33,
    sizes={'emptybarb': 0},     # sin circulito de calma
    transform=ccrs.PlateCarree(),
)

# Escala textual (compacta, sin 'kts'), pegada a la izquierda
scale_vals = [5,10,15,20,25,30,35,40,45,50,55,60]
x0, x1 = 0.02, 0.48
y = -0.055
xs = np.linspace(x0, x1, len(scale_vals))
for xv, sv in zip(xs, scale_vals):
    ax.text(xv, y, f"{sv}", transform=ax.transAxes, fontweight="bold",
            ha="center", va="center", fontsize=9, color=cmap(norm(sv)))

valid_time = np.datetime_as_string(u850.time.values, unit="h")
ax.set_title(f"Wind 850 hPa [kts] • {valid_time} UTC", loc="left", fontsize=11)
ax.set_title("ERA5", loc="right", fontsize=11)

plt.tight_layout()
plt.savefig(OUTFILE, bbox_inches="tight")
print(f"[OK] Figura guardada en: {OUTFILE}")
