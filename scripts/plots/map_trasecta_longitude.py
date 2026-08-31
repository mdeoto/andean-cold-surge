#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import os
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cfgrib  # engine para xarray

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
GRIB = PLEV_GRIB
OUT_PNG = FIG_DIR / "xsec_lon-69p5_lat-height_theta_v_w.png"



# =========================
# PATHS / I/O
# =========================



# =========================
# CONFIG
# =========================
TIDX        = int(os.environ.get("TIDX", "16"))     # índice temporal
LON_FIXED   = float(os.environ.get("LON_FIXED", "-69.5"))
LAT_MIN     = float(os.environ.get("LAT_MIN", "-45"))
LAT_MAX     = float(os.environ.get("LAT_MAX", "-35"))

STRIDE_LAT  = int(os.environ.get("STRIDE_LAT", "1"))
STRIDE_LEV  = int(os.environ.get("STRIDE_LEV", "1"))

# Escalas para w independiente del eje
W_REF   = float(os.environ.get("W_REF",  "0.1"))   # m/s que representa la referencia del quiverkey
FRAC    = float(os.environ.get("FRAC",   "0.075")) # fracción de altura de eje usada para W_REF
# Quiver usa scale_units='height' y scale=1.0 -> longitud dibujada = FRAC*(w/W_REF)

# Umbral de calma para v (en nudos, se aplica a |v| meridional)
V_MIN_KT    = float(os.environ.get("V_MIN_KT", "2.0"))

# =========================
# Paleta para θ (tu escala °C → K)
# =========================
temp_values = np.array([
    -28,-26,-24,-22,-20,-18,-16,-14,-12,-10,-8,-6,-4,-2, 0, 2, 4, 6, 8,10,
     12, 14, 16, 18, 20, 22, 24, 26,28,30,32,34,36,38,40,42,44,46,48
], dtype=float)

temp_colors = [
    "#666666","#888888","#b0b0b0","#cccccc","#e4e4e4",
    "#773377","#aa33aa","#cc33cc","#ff33ff","#ff99ff",
    "#1500cc","#3366ff","#3399ff","#33ccff","#33ffff",
    "#007700","#009900","#00bb00","#00dd00","#00ff00",
    "#ffff33","#ffee33","#ffdd33","#ffcc33","#ffbb33","#ffaa00","#ff9900",
    "#ff7700","#ff0000","#ee0000","#cc0000","#bb0000","#aa0000","#990000",
    "#880000","#720000","#5b0000","#420000","#1d0000"
]
theta_bounds = temp_values + 273.15
cmap_temp = mcolors.ListedColormap(temp_colors)
norm_temp = mcolors.BoundaryNorm(theta_bounds, cmap_temp.N + 1, extend="both")

# =========================
# Utilidades
# =========================
def potential_temperature(Tk, p_hPa):
    p0 = 1000.0
    Rd_cp = 0.2854
    return Tk * (p0 / p_hPa) ** Rd_cp

def omega_to_w(omega_Pa_s, T_K, p_hPa):
    """ω (Pa/s) → w (m/s), ascenso > 0"""
    R = 287.0; g = 9.80665
    p_Pa = p_hPa * 100.0
    return - (omega_Pa_s * R * T_K) / (p_Pa * g)

# =========================
# Carga ERA5
# =========================
ds = xr.open_dataset(GRIB, engine="cfgrib")

# Ordenar latitudes ascendentes (S→N a la derecha)
if np.any(np.diff(ds["latitude"].values) < 0):
    ds = ds.sortby("latitude")

lev_name = "isobaricInhPa" if "isobaricInhPa" in ds.dims else "level"
g0 = 9.80665

# Selección temporal
time_val = ds["time"].isel(time=TIDX)
ds_t = ds.sel(time=time_val)

# Longitud más cercana
lon_vals = ds_t["longitude"].values
lon_idx = int(np.argmin(np.abs(lon_vals - LON_FIXED)))
lon_sel = float(lon_vals[lon_idx])
print(f"[i] Longitud solicitada: {LON_FIXED:.2f}°, usando rejilla: {lon_sel:.2f}°")

# Corte latitudinal
ds_line = ds_t.sel(longitude=lon_sel, latitude=slice(LAT_MIN, LAT_MAX))

# Variables en corte
p_hPa   = ds_line[lev_name].values                 # (lev,)
T_K     = ds_line["t"].squeeze().values            # (lev, lat)
V_ms    = ds_line["v"].squeeze().values            # (lev, lat)
U_ms    = ds_line["u"].squeeze().values            # (lev, lat)
Omega   = ds_line["w"].squeeze().values            # (lev, lat) Pa/s
Z_gpot  = ds_line["z"].squeeze().values            # (lev, lat) m^2 s^-2

# Altura geométrica (m)
H_m = Z_gpot / g0                                  # (lev, lat)

# Theta [K]
theta = potential_temperature(T_K, p_hPa[:, None])

# w en m/s
w_ms = omega_to_w(Omega, T_K, p_hPa[:, None])

# Grids
lat = ds_line["latitude"].values                   # (lat,)
# Usamos los campos 2D reales
LAT2D, _ = np.meshgrid(lat, p_hPa)                 # sólo para replicar lat en 2D
H2D = H_m.copy()                                   # (lev, lat) en m

# =========================
# Plot
# =========================
fig, ax = plt.subplots(figsize=(10.2, 6.0), dpi=140)

# θ sombreado en lat-altura
pcm = ax.pcolormesh(LAT2D, H2D, theta, cmap=cmap_temp, norm=norm_temp, shading="auto")

# Contornos de θ
th_min = float(np.nanpercentile(theta, 5))
th_max = float(np.nanpercentile(theta, 95))
th_lvls = np.arange(np.floor(th_min/2)*2, np.ceil(th_max/2)*2 + 0.1, 2.0)
cs = ax.contour(LAT2D, H2D, theta, levels=th_lvls, colors="k", linewidths=0.7, alpha=0.7)
ax.clabel(cs, fmt="%.0f", fontsize=8)

# -------------------------
# BARBAS (u,v) en plano (lat,z) como “mapa 2D” + HS + sin calmas si |v|<V_MIN_KT
# -------------------------
MS2KT = 1.9438444924406048
ii = slice(None, None, STRIDE_LEV)
jj = slice(None, None, STRIDE_LAT)

LATs = LAT2D[ii, jj]      # x = lat
Zs   = H2D[ii, jj]        # y = altura (m)
Uq   = U_ms[ii, jj]       # u en m/s
Vq   = V_ms[ii, jj]       # v en m/s

# Filtro por umbral sólo en |v| (meridional)
mask = (np.abs(Vq) * MS2KT) >= V_MIN_KT

x_plot = LATs[mask]
y_plot = Zs[mask]
u_plot = (Uq[mask] * MS2KT)    # U en kt (este-oeste)
v_plot = (Vq[mask] * MS2KT)    # V en kt (norte-sur)

ax.barbs(
    x_plot, y_plot, u_plot, v_plot,
    flip_barb=True,             # convención Hemisferio Sur
    pivot="middle",
    length=4.2, linewidth=0.45,
    sizes={'emptybarb': 0},     # sin circulito de calma
    color="black", zorder=3,
)

# =========================
# QUIVER de w NEGRO, intercalado ENTRE NODOS (centros)
#   - independencia de escala del eje: scale_units='height', scale=1.0
#   - posiciones: centros bilineales (reduce “solapado” con barbas)
# =========================
# Centramos en lat y z: (lev-1, lat-1)
LATc = 0.5 * (LAT2D[:, 1:] + LAT2D[:, :-1])     # (lev, lat-1)
Zc   = 0.5 * (H2D[1:, :]   + H2D[:-1, :])       # (lev-1, lat)
# Centro bilineal (lev-1, lat-1)
LATc = 0.5 * (LATc[1:, :] + LATc[:-1, :])
Zc   = 0.5 * (Zc[:, 1:]   + Zc[:, :-1])

# w escalado a fracción de altura del eje
Vdisp = (w_ms / W_REF) * FRAC                   # (lev, lat)
# Centro de w
Wc = 0.25 * (Vdisp[:-1, :-1] + Vdisp[1:, :-1] + Vdisp[:-1, 1:] + Vdisp[1:, 1:])

# Submuestreo coherente con barbas (strides)
LATc_s = LATc[::STRIDE_LEV, ::STRIDE_LAT]
Zc_s   = Zc[::STRIDE_LEV, ::STRIDE_LAT]
Wc_s   = Wc[::STRIDE_LEV, ::STRIDE_LAT]
Uzero  = np.zeros_like(Wc_s)

Qw = ax.quiver(
    LATc_s, Zc_s,
    Uzero, Wc_s,
    angles='xy',
    scale_units='height',  # longitud indep. del eje (fracción de altura)
    scale=1.0,
    width=0.0014, headwidth=3.6, headlength=5.0, headaxislength=4.6,
    color="black", alpha=0.95, zorder=4
)

# Clave de escala para w: W_REF → FRAC de la altura del eje
ax.quiverkey(
    Qw, 0.92, -0.08, FRAC, f"{W_REF:.1f} m/s",
    labelpos='E', coordinates='axes',
    color="black", labelcolor="black",
    fontproperties={'size': 9, 'weight': 'bold'}
)

# Ejes y formato
ax.set_xlim(LAT_MIN, LAT_MAX)
ax.set_ylim(0, 4000)  # 0–4000 m
ax.set_xlabel("Latitud (°)")
ax.set_ylabel("Altura (m)")
valid_time = np.datetime_as_string(time_val.values, unit='h')
ax.set_title(f"Sección lon {lon_sel:.2f}°: θ (sombreado), barbas (HS), w-quiver intercalado\n{valid_time} UTC",
             fontsize=12)

plt.tight_layout()
plt.savefig(OUT_PNG, bbox_inches="tight")
print("[OK] Figura guardada en:", OUT_PNG)
