# Andean Cold Surge

ERA5-based analysis of cold-air surges and quasi-stationary cold-air structures east of the Andes in subtropical South America.

This repository contains a reproducible workflow to download ERA5 data, construct hour-of-day climatologies, calculate event anomalies, and diagnose the synoptic and vertical structure of selected cold-air events.

The project focuses particularly on situations in which a shallow cold-air mass remains quasi-stationary over northern Patagonia instead of undergoing the more classical rapid equatorward propagation observed in South American cold surges.

---

## Scientific motivation

Cold-air surges east of the Andes are a recurrent feature of the atmospheric circulation over South America.

The classical conceptual model involves an equatorward displacement of cold air along the eastern slope of the Andes, where the mountain barrier strongly constrains the low-level circulation and favors meridional propagation.

Some events, however, show a substantially different evolution.

A shallow cold-air mass can remain nearly stationary over northern Patagonia while persistent northerly or northeasterly flow develops immediately to its north and east. In such situations, the cold dome may persist for several days despite the existence of a strong horizontal temperature contrast.

This behavior raises several questions:

- Why does the cold air fail to propagate rapidly northward?
- What role does the background northerly flow play?
- How important is the anticyclonic circulation over central-eastern Argentina?
- How shallow is the cold-air structure?
- What processes maintain or erode the cold dome?
- Can the event be interpreted as a classical cold surge, or does it require an additional dynamical framework?

The project is designed to address these questions using ERA5 reanalysis and event-based diagnostics.

---

## Scientific background

A major reference for the project is the conceptual framework of South American cold surges described by Garreaud (2000), where the Andes strongly influence the propagation and structure of cold air east of the mountain range.

The current work extends that perspective toward events characterized by a slower or quasi-stationary evolution over northern Patagonia.

Rather than assuming a single dynamical explanation, the project compares the observed atmospheric structure against several possible mechanisms.

---

## Working hypothesis

The working hypothesis is that some cold-air structures east of the Andes cannot be understood solely as freely propagating cold surges.

Their evolution may result from the interaction among:

- cold-air propagation along the eastern slope of the Andes;
- persistent low-level northerly or northeasterly background flow;
- anticyclonic circulation downstream over central and eastern Argentina;
- strong static stability within the shallow cold-air mass;
- topographic trapping associated with the Andes;
- horizontal cold-air advection;
- vertical motion and diabatic processes.

One dynamical interpretation to be tested is whether part of the disturbance behaves similarly to a topographically trapped wave.

In a simplified framework, the observed propagation velocity may be interpreted as the combination of an intrinsic propagation speed and the background flow:

```text
C_observed ≈ C_intrinsic + U_background

For example, an intrinsically northward-propagating disturbance may become nearly stationary if an opposing northerly background flow has a comparable magnitude.

A conceptual case such as

C_intrinsic  ≈ +12 m s-1
U_background ≈ -15 m s-1

would yield a small or slightly southward net propagation speed.

This possible terrain-trapped or Kelvin-like interpretation is treated strictly as a hypothesis to be evaluated against the atmospheric diagnostics, rather than as an assumed explanation.

Research questions

The workflow is intended to address questions such as:

What distinguishes quasi-stationary cold-air structures from classical Andean cold surges?
What controls the propagation speed of the cold-air boundary?
How important is the opposing low-level background flow?
What role does the downstream anticyclone play in maintaining the cold-air dome?
How does the depth of the cold air evolve during the event?
Is the cold anomaly mainly maintained by horizontal advection?
What is the contribution of vertical motion?
How important are diabatic processes?
Does the disturbance exhibit characteristics consistent with a topographically trapped wave?
Under what synoptic configurations does the cold-air mass propagate northward, remain stationary, or retreat?
Case-study strategy

Events are defined using a central reference date, referred to as day 0.

For each event, ERA5 fields are downloaded over a five-day window:

day -2  →  day -1  →  day 0  →  day +1  →  day +2

with a temporal resolution of 3 hours.

The central date is supplied using the environment variable:

export EVENT_DAYS0="2023-07-17"

Multiple events can be supplied as comma-separated dates:

export EVENT_DAYS0="2023-07-17,2025-07-20"

The event window can be changed with:

export PAD_DAYS=2

The event catalogue is intended to support comparisons between quasi-stationary cold-air episodes and more classical cold-surge configurations.

ERA5 domains

Two complementary ERA5 domains are used.

Large domain
North: 15°S
South: 65°S
West:  100°W
East:   30°W

This domain provides the synoptic-scale context over South America and the adjacent Pacific and Atlantic oceans.

It is used to analyze the large-scale pressure field, circulation patterns, upper-level forcing, and the synoptic environment associated with the cold surge.

Small dense domain
North: 30°S
South: 45°S
West:  75°W
East:   60°W

This domain focuses on the Andes, northern Patagonia, and central Argentina.

It uses a denser set of pressure levels in the lower and middle troposphere to better resolve the vertical structure of the cold-air dome.

ERA5 variables
Pressure-level variables

The workflow downloads:

geopotential;
temperature;
zonal wind;
meridional wind;
specific humidity;
vertical velocity.

The large domain uses selected standard pressure levels:

1000
925
850
700
500
250 hPa

The small dense domain uses closely spaced pressure levels between approximately 1000 and 500 hPa, complemented by upper-level fields at 300 and 250 hPa.

The dense vertical sampling is intended to characterize:

cold-dome depth;
inversion strength;
lower-tropospheric stability;
vertical circulation;
along-barrier flow;
cross-barrier structure.
Single-level variables

The ERA5 single-level fields include:

10 m zonal wind;
10 m meridional wind;
2 m temperature;
mean sea-level pressure;
sea-surface temperature;
low-cloud cover;
total precipitation;
snowfall;
sea-ice cover;
land-sea mask.
Hour-of-day climatology

The event analysis is complemented by an ERA5 hour-of-day climatology covering:

1991–2020

For each month and UTC hour, monthly averaged reanalysis fields are downloaded independently for each year.

The workflow then constructs the 30-year mean:

ERA5 HOD fields
      │
      ├── 1991
      ├── 1992
      ├── ...
      └── 2020
            │
            ▼
     1991–2020 HOD mean

This approach preserves the mean atmospheric state associated with each UTC hour.

Event anomalies can therefore be calculated relative to the climatological state corresponding to the same time of day rather than against a simple daily or monthly mean.

Conceptually:

event anomaly =
event field
-
1991–2020 climatological field at the same UTC hour
Processing workflow

The current workflow is:

            ERA5
              │
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
 event download   HOD climatology
       │          1991–2020
       │             │
       │             ▼
       │       multi-year means
       │             │
       └──────┬──────┘
              │
              ▼
        event anomalies
              │
              ▼
     dynamical diagnostics
              │
              ▼
       maps / cross-sections

The workflow intentionally separates:

data acquisition;
climatological processing;
event anomaly calculation;
scientific visualization and diagnosis.
Repository structure
andean-cold-surge/
├── config/
│   └── transecta.kml
│
├── docs/
│
├── env/
│   ├── environment.yml
│   ├── environment-history.yml
│   └── environment-linux-64-explicit.txt
│
├── scripts/
│   ├── download/
│   │   ├── download_events_large.py
│   │   ├── download_events_small_dense.py
│   │   ├── download_climatology_hod_large.py
│   │   └── download_climatology_hod_small_dense.py
│   │
│   ├── processing/
│   │   ├── build_multiyear_means.py
│   │   └── compute_anomalies_events.py
│   │
│   ├── plots/
│   │   ├── map_500hPa.py
│   │   ├── map_700hPa.py
│   │   ├── map_850hPa.py
│   │   ├── map_wind_850hPa.py
│   │   ├── map_jet_300hPa.py
│   │   ├── map_trasecta.py
│   │   └── map_trasecta_longitude.py
│   │
│   ├── run_download_events.sh
│   ├── run_download_climatology.sh
│   ├── run_process_climatology.sh
│   └── run_compute_anoms.sh
│
├── .gitignore
└── README.md

ERA5 files, generated figures, temporary files, and logs are deliberately excluded from version control.

Conda environment

The original analysis workflow was developed and tested using the newocean Conda environment.

The repository contains three complementary environment descriptions under env/.

Standard environment
conda env create -f env/environment.yml
Environment reconstructed from explicitly requested packages
conda env create -f env/environment-history.yml
Exact Linux package specification

For a platform-compatible reconstruction:

conda create --name andean-cold-surge \
    --file env/environment-linux-64-explicit.txt

The main scientific Python dependencies include:

cdsapi
xarray
pandas
numpy
cfgrib
eccodes
matplotlib
cartopy
metpy
pyproj
NetCDF support

The plotting workflow requires MetPy for some vertical cross-section diagnostics.

ERA5 and Copernicus CDS configuration

ERA5 data are obtained from the Copernicus Climate Data Store using the Python cdsapi client.

Before running the download scripts, the user must:

create an account in the Copernicus Climate Data Store;
accept the required ERA5 dataset licences and terms;
configure the CDS API credentials locally.

The CDS API configuration is stored outside this repository in:

~/.cdsapirc

The file must contain the API configuration associated with the user's Copernicus account.

CDS credentials must never be committed to this repository.

The connection can be tested with:

python -c "import cdsapi; cdsapi.Client(); print('CDS configuration OK')"

The download scripts instantiate:

cdsapi.Client()

and therefore use the external CDS configuration automatically.

Data directory

By default, downloaded and processed files are stored under:

data/

The data location can be changed without modifying the source code:

export COLD_SURGE_BASEDIR=/path/to/era5/data

This is recommended when ERA5 files are stored on a large filesystem outside the Git repository.

Downloading an event

Define the central date:

export EVENT_DAYS0="2023-07-17"

Optionally define the event padding:

export PAD_DAYS=2

Run:

./scripts/run_download_events.sh

The workflow downloads both:

large domain
small dense domain

for the corresponding event period.

Downloading the climatology

Select the months to process:

export MONTHS="7,8,9"

Run:

./scripts/run_download_climatology.sh

The download generates hour-of-day climatological ERA5 fields for every year between 1991 and 2020.

Because this represents a substantial amount of data, the climatology downloads may be run independently and monitored through the generated log files.

Building the 1991–2020 climatological means

Once the yearly hour-of-day files are available:

./scripts/run_process_climatology.sh

The processing script concatenates the individual years and calculates the multi-year mean for each month and hour of day.

Computing event anomalies

Once both the event fields and the corresponding climatological means are available:

./scripts/run_compute_anoms.sh

The resulting anomaly fields represent:

event state - corresponding HOD climatology

and retain the full temporal evolution of the event.

Plot configuration

The plotting scripts can be applied to different event windows without changing the Python source code.

An event is selected using:

export EVENT_TAG="202507_20250718_20250722"

The expected naming convention is:

YYYYMM_YYYYMMDD_YYYYMMDD

For example:

202507_20250718_20250722

corresponds to an event dataset stored under:

data/events_small_dense/202507/202507_20250718_20250722/

The expected pressure-level file is:

eventsS_pressure_202507_20250718_20250722.grib

and, when required:

eventsS_surface_202507_20250718_20250722.grib

The scripts retain historical example events as default values, but these can be overridden through EVENT_TAG.

Figure output

Figures are written by default to:

figs/era5/

An alternative output root can be defined through:

export COLD_SURGE_FIGDIR=/path/to/figures

Generated figures are not tracked by Git.

Diagnostic plots

The current plotting workflow includes several complementary diagnostics.

850 hPa
map_850hPa.py

Analyzes lower-tropospheric temperature together with the surface pressure field.

850 hPa wind
map_wind_850hPa.py

Diagnoses the low-level flow associated with the cold-air structure and the background circulation.

700 hPa
map_700hPa.py

Analyzes temperature and geopotential height in the middle-lower troposphere.

500 hPa
map_500hPa.py

Provides the mid-tropospheric synoptic environment.

300 hPa jet
map_jet_300hPa.py

Diagnoses upper-level geopotential height and wind speed.

Longitude-height cross-section
map_trasecta_longitude.py

Generates a vertical section through the dense ERA5 domain to analyze thermodynamic structure and vertical motion.

Arbitrary transect
map_trasecta.py

Generates a cross-section following a user-defined geographical transect.

The transect geometry is stored in:

config/transecta.kml

This file is version-controlled because the geometry forms part of the scientific configuration of the diagnostic rather than part of the generated ERA5 dataset.

Vertical-structure diagnostics

The cross-section analysis is particularly important for identifying the structure of the cold dome.

Variables derived or analyzed in the vertical sections include:

potential temperature;
along-section wind;
vertical velocity;
static stability;
depth of the cold-air layer.

These diagnostics are intended to determine whether the cold anomaly is restricted to a shallow boundary-layer-like structure or extends through a deeper fraction of the troposphere.

Dynamical interpretation

The analysis is designed to examine several potentially interacting processes.

Topographic constraint

The Andes provide a major meridional barrier that strongly modifies the low-level flow.

Horizontal advection

Cold-air advection along the eastern slope of the Andes is expected to be an important component of the cold-surge evolution.

Background northerly flow

Persistent northerly or northeasterly flow may oppose the intrinsic propagation of the cold-air disturbance and contribute to its quasi-stationary behavior.

Downstream anticyclone

A persistent anticyclonic circulation over central-eastern Argentina or the western South Atlantic may help maintain northerly flow north of the cold dome and inhibit its equatorward advance.

Vertical structure

Strong stability and a pronounced inversion can dynamically isolate the shallow cold-air mass from the free troposphere.

Terrain-trapped disturbances

One hypothesis under investigation is whether some events exhibit behavior consistent with a disturbance trapped against the eastern slope of the Andes.

This hypothesis requires further dynamical testing and is not assumed a priori.

Planned diagnostics

Future analyses may include:

objective tracking of the cold-air boundary;
propagation-speed calculations;
Lagrangian temperature tendency;
decomposition of horizontal and vertical temperature advection;
low-level momentum balance;
composites of propagating versus quasi-stationary events;
comparison of anticyclone configurations;
cold-dome polygon identification;
terrain-following diagnostics;
testing of terrain-trapped or Kelvin-like propagation frameworks.

These diagnostics are intended to distinguish descriptive similarities from dynamically supported mechanisms.

Reproducibility philosophy

This repository contains code and analysis configuration, rather than bulk atmospheric datasets.

The intended workflow is:

code + configuration
        │
        ▼
Copernicus CDS
        │
        ▼
ERA5 data
        │
        ▼
processing
        │
        ▼
diagnostics

Large binary ERA5 files can therefore be reconstructed from the download scripts rather than stored in Git.

Local filesystem paths are not hard-coded in the workflow.

Project-specific locations can be controlled using environment variables such as:

COLD_SURGE_BASEDIR
COLD_SURGE_FIGDIR
EVENT_DAYS0
EVENT_TAG
MONTHS
PAD_DAYS
Current status

The repository currently provides:

ERA5 event downloads;
ERA5 hour-of-day climatology downloads;
1991–2020 multi-year climatological means;
event anomaly calculations;
synoptic maps;
lower-, middle-, and upper-tropospheric diagnostics;
vertical cross-sections;
portable data and figure paths;
reproducible Conda environment descriptions.

The scientific analysis remains under active development.

In particular, the interpretation of quasi-stationary cold-air structures and their possible relationship with topographically trapped disturbances remains a research question rather than a final conclusion.

Data source

Atmospheric data are obtained from:

ERA5 — ECMWF Reanalysis v5

through the Copernicus Climate Change Service Climate Data Store.

Raw and processed ERA5 datasets are not distributed with this repository because of their size.

The included download scripts provide the basis for reproducing the atmospheric datasets used by the project.

Reference

Garreaud, R. D. (2000).

Cold air incursions over subtropical South America: mean structure and dynamics.

Monthly Weather Review, 128, 2544–2559.

Author

Matías De Oto
