#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import os, re
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import cfgrib  # engine para xarray
from metpy.interpolate import cross_section
from pyproj import Geod

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



# =========================
# PATHS (caso 202307)
# =========================


KML_PATH = PROJECT_DIR / "config" / "transecta.kml"

GRIB = PLEV_GRIB



OUT_PNG = FIG_DIR / "xsec_theta_ualong_w.png"

# =========================
# CONFIG
# =========================
TIDX = int(os.environ.get("TIDX", "0"))            # índice temporal
N_ALONG = int(os.environ.get("N_ALONG", "250"))    # puntos a lo largo
W_SCALE = float(os.environ.get("W_SCALE", "90.0")) # escala visual quiver
W_MIN = float(os.environ.get("W_MIN", "0.02"))     # umbral |w| (m/s) para dibujar
ANISO = float(os.environ.get("ANISO", "10.0"))     # 10 m/s horiz ≈ 1 m/s vert

# =========================
# Utilidades
# =========================
def read_kml_coords(kml_path):
    with open(kml_path, "r", encoding="utf-8") as f:
        txt = f.read()
    m = re.search(r"<coordinates>(.*?)</coordinates>", txt, flags=re.DOTALL)
    if not m:
        raise RuntimeError(f"No encontré <coordinates> en {kml_path}")
    coords = []
    for chunk in m.group(1).strip().split():
        p = chunk.split(",")
        if len(p) >= 2:
            coords.append((float(p[0]), float(p[1])))
    if len(coords) < 2:
        raise RuntimeError("Se requieren al menos 2 puntos para la transecta.")
    return np.array(coords)

def densify_track(lonlat, n_total=250):
    geod = Geod(ellps="WGS84")
    dists = [0.0]
    for i in range(1, len(lonlat)):
        _, _, m = geod.inv(lonlat[i-1,0], lonlat[i-1,1], lonlat[i,0], lonlat[i,1])
        dists.append(dists[-1] + m)
    dists = np.array(dists)
    s_target = np.linspace(0, dists[-1], n_total)
    lon_out = np.interp(s_target, dists, lonlat[:,0])
    lat_out = np.interp(s_target, dists, lonlat[:,1])
    return lon_out, lat_out, s_target  # m

def potential_temperature(Tk, p_hPa):
    p0 = 1000.0
    Rd_cp = 0.2854
    return Tk * (p0 / p_hPa) ** Rd_cp

def omega_to_w(omega_Pa_s, T_K, p_hPa):
    R = 287.0; g = 9.80665
    p_Pa = p_hPa * 100.0
    return - (omega_Pa_s * R * T_K) / (p_Pa * g)  # m/s (ascenso > 0)

def project_wind_along(u, v, azimuth_deg):
    th = np.deg2rad(azimuth_deg)
    ex = np.sin(th); ey = np.cos(th)
    return u * ex + v * ey

def corners_from_centers(C2D: np.ndarray) -> np.ndarray:
    """Convierte centros (n,m) a esquinas (n+1,m+1) aptas para pcolormesh."""
    Cp = np.pad(C2D, ((1, 1), (1, 1)), mode='edge')  # replica bordes
    return 0.25 * (Cp[:-1, :-1] + Cp[:-1, 1:] + Cp[1:, :-1] + Cp[1:, 1:])

# =========================
# Carga ERA5 presión (MetPy 1.5.1 compatible)
# =========================
print("[i] Abriendo GRIB:", GRIB)
ds = xr.open_dataset(GRIB, engine="cfgrib")

# Ordenar latitud ascendente
if np.any(np.diff(ds["latitude"].values) < 0):
    ds = ds.sortby("latitude")

# Parse CF + marcar ejes (MetPy 1.5.1)
ds = ds.metpy.parse_cf()
ds["latitude"].attrs.update({"standard_name":"latitude","units":"degrees_north","axis":"Y"})
ds["longitude"].attrs.update({"standard_name":"longitude","units":"degrees_east","axis":"X"})

lev_name = "isobaricInhPa" if "isobaricInhPa" in ds.dims else "level"

# Seleccionar tiempo ANTES del cross_section
time_val = ds["time"].isel(time=TIDX)
ds_t = ds.sel(time=time_val)

# =========================
# Transecta S→N (Sur a la izquierda, Norte a la derecha)
# =========================
lonlat = read_kml_coords(KML_PATH)
lons_along, lats_along, s_m = densify_track(lonlat, n_total=N_ALONG)

# Forzar orientación S -> N (lat start < lat end). Si no, invertimos.
if not (lats_along[0] < lats_along[-1]):
    lons_along = lons_along[::-1]
    lats_along = lats_along[::-1]

geod = Geod(ellps="WGS84")
az_f, _, _ = geod.inv(lons_along[0], lats_along[0], lons_along[-1], lats_along[-1])
azimuth_deg = az_f

# =========================
# Cross section (MetPy 1.5.1, sin path)
# =========================
sec = cross_section(
    ds_t,
    start=(float(lats_along[0]),  float(lons_along[0])),
    end=(  float(lats_along[-1]), float(lons_along[-1])),
    steps=N_ALONG
).set_coords(("latitude","longitude"))

# Distancia acumulada (km) a lo largo (ya S→N)
dist_km = np.zeros(N_ALONG)
for i in range(1, N_ALONG):
    _, _, m = geod.inv(lons_along[i-1], lats_along[i-1], lons_along[i], lats_along[i])
    dist_km[i] = dist_km[i-1] + m/1000.0
sec = sec.assign_coords(distance_km=("index", dist_km))

# =========================
# Derivados: θ, w(m/s), H, u_along
# =========================
p_hPa = sec[lev_name].values                 # (lev,)
T_K   = sec["t"].values                      # (lev, index)
theta = potential_temperature(T_K, p_hPa[:, None])

g0 = 9.80665
H_m = sec["z"].values / g0                   # (lev, index)

u_ms = sec["u"].values
v_ms = sec["v"].values
u_along = project_wind_along(u_ms, v_ms, azimuth_deg)

omega_Pa_s = sec["w"].values
w_ms = omega_to_w(omega_Pa_s, T_K, p_hPa[:, None])
w_ms_mask = np.where(np.abs(w_ms) >= W_MIN, w_ms, np.nan)

# =========================
# Coordenadas 2D + edges
# =========================
dist = sec["distance_km"].values             # (index,)
nlev, nidx = theta.shape                     # C: (nlev, nidx)
X2D = np.tile(dist, (nlev, 1))               # (nlev, nidx)
Y2D = (H_m / 1000.0)                         # (nlev, nidx) en km

Xedges = corners_from_centers(X2D)           # (nlev+1, nidx+1)
Yedges = corners_from_centers(Y2D)

# =========================
# Plot
# =========================
fig, ax = plt.subplots(figsize=(11.5, 5.2), dpi=140)

# Sombreado θ
th_min = float(np.nanpercentile(theta, 5))
th_max = float(np.nanpercentile(theta, 95))
levels_th = np.linspace(th_min, th_max, 21)
cmap_th = plt.get_cmap("Spectral_r")

mesh = ax.pcolormesh(Xedges, Yedges, theta,
                     shading="flat",             # usamos edges → sin warning
                     cmap=cmap_th,
                     norm=mcolors.BoundaryNorm(levels_th, 256))

# Isolíneas θ (centers)
cs_theta = ax.contour(X2D, Y2D, theta,
                      levels=np.arange(np.floor(th_min/2)*2, np.ceil(th_max/2)*2+0.1, 4),
                      colors="k", linewidths=0.8, alpha=0.7)
ax.clabel(cs_theta, fmt="%.0f", fontsize=8)

# Quiver anisotrópico: 10× vertical (por defecto)
stride_x = max(1, int(N_ALONG/60))
stride_z = max(1, int(len(p_hPa)/22))
Xq = X2D[::stride_z, ::stride_x]
Yq = Y2D[::stride_z, ::stride_x]
Uq = u_along[::stride_z, ::stride_x]
Wq = w_ms_mask[::stride_z, ::stride_x]

Uq_plot = Uq
Wq_plot = Wq * ANISO

mask = ~np.isnan(Wq_plot)
ax.quiver(Xq[mask], Yq[mask], Uq_plot[mask], Wq_plot[mask],
          angles='xy', scale_units='xy', scale=W_SCALE,
          width=0.0026, headwidth=3.8, headlength=5.2, headaxislength=4.8,
          color="black", alpha=0.9, zorder=3)

# Ejes, límites y títulos
ax.set_xlabel("Distancia a lo largo de la transecta (km)  [Sur → Norte]")
ax.set_ylabel("Altura (km)")
ax.set_ylim(0, 4.0)  # límite solicitado
valid_time = np.datetime_as_string(time_val.values, unit='h')
ax.set_title(f"Sección vertical (caso 202307): θ sombreado + quiver (u_along, w×{ANISO:.0f})\n{valid_time} UTC",
             fontsize=12)

# Texto de extremos
ax.text(0.0, 1.02, f"Sur (ini): {lats_along[0]:.2f}°, {lons_along[0]:.2f}°",
        transform=ax.transAxes, ha="left", va="bottom", fontsize=8,
        path_effects=[pe.withStroke(linewidth=2, foreground='white')])
ax.text(1.0, 1.02, f"Norte (fin): {lats_along[-1]:.2f}°, {lons_along[-1]:.2f}°",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
        path_effects=[pe.withStroke(linewidth=2, foreground='white')])

# Recordatorio de escala anisotrópica
ax.text(0.01, -0.08, f"Escala quiver: {ANISO:.0f}× vertical (10 m/s ↔ ≈ 1 m/s ↕)",
        transform=ax.transAxes, ha="left", va="center", fontsize=8)

plt.tight_layout()
plt.savefig(OUT_PNG, bbox_inches="tight")
print(f"[OK] Sección guardada en:", OUT_PNG)

