# Andean Cold Surge

ERA5-based analysis of cold-air surges and quasi-stationary cold-air structures east of the Andes in subtropical South America.

This repository contains the reproducible workflow used to download ERA5 data, construct hour-of-day climatologies, calculate event anomalies, and diagnose the three-dimensional structure and evolution of selected cold-air events.

## Scientific motivation

Cold-air surges east of the Andes are a recurrent feature of the South American circulation. Their classical conceptual model involves the equatorward propagation of cold air along the eastern slope of the Andes, strongly influenced by the topographic barrier.

Some events, however, show a less classical evolution.

Instead of rapidly propagating northward, a shallow cold-air mass can remain quasi-stationary over northern Patagonia while persistent northerly or northeasterly flow develops immediately to its north and east. This configuration raises questions about the mechanisms controlling the propagation, retention, and eventual erosion of the cold-air dome.

The project therefore investigates the distinction between:

1. classical equatorward-propagating cold surges east of the Andes; and
2. quasi-stationary or slowly propagating cold-air structures over northern Patagonia.

A central objective is to determine which synoptic and mesoscale mechanisms can explain the persistence of the latter.

## Working hypothesis

The working hypothesis is that some cold-air structures east of the Andes cannot be interpreted solely as freely propagating cold surges.

Their evolution may result from the interaction among:

- cold-air propagation along the eastern Andean slope;
- low-level northerly or northeasterly background flow;
- persistent anticyclonic circulation downstream over central-eastern Argentina;
- topographic trapping by the Andes;
- vertical stability and the shallow character of the cold-air dome.

One dynamical interpretation to be tested is whether part of the disturbance behaves similarly to a topographically trapped wave.

In a simplified framework, the observed propagation may be understood as the combination of an intrinsic propagation speed and the opposing background flow:

```text
C_observed ≈ C_intrinsic + U_background

A sufficiently strong northerly background flow could substantially reduce the northward propagation speed, produce a nearly stationary structure, or even lead to apparent retrogression.

This interpretation is treated as a hypothesis to be evaluated against ERA5 diagnostics rather than as an a priori explanation.

Case-study strategy

Events are defined by a central reference date (day 0).

For each event, ERA5 fields are downloaded over a five-day window:

day -2  →  day -1  →  day 0  →  day +1  →  day +2

with a temporal resolution of 3 hours.

The reference date can be supplied through the environment variable:

export EVENT_DAYS0="2023-07-17"

Multiple events can be provided as comma-separated dates.

The event catalogue is intended to support comparison between quasi-stationary cold-air episodes and more classical cold-surge configurations.

ERA5 domains

Two complementary domains are used.

Large domain
North: 15°S
South: 65°S
West:  100°W
East:   30°W

This domain provides the synoptic-scale context over South America and the adjacent oceans.

Small dense domain
North: 30°S
South: 45°S
West:  75°W
East:  60°W

This domain focuses on the Andes and northern Patagonia and uses a denser set of pressure levels to diagnose the vertical structure of the cold-air mass.

Variables

ERA5 pressure-level fields include:

geopotential;
temperature;
zonal wind;
meridional wind;
specific humidity;
vertical velocity.

The large-domain analysis uses selected pressure levels from the lower troposphere to the upper troposphere.

The small dense domain uses closely spaced levels between 1000 and 500 hPa, complemented by upper-level fields at 300 and 250 hPa.

ERA5 single-level variables include:

10 m zonal and meridional wind;
2 m temperature;
mean sea-level pressure;
sea-surface temperature;
low-cloud cover;
total precipitation;
snowfall;
sea-ice cover;
land-sea mask.
Hour-of-day climatology

The event analysis is complemented by an ERA5 hour-of-day (HOD) climatology for 1991–2020.

For each month, year, and UTC hour, monthly averaged reanalysis fields are downloaded independently.

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

This provides a climatological reference that preserves the time-of-day dependence of the atmospheric state.

Event anomalies are subsequently calculated relative to the climatological field corresponding to the same UTC hour.

Workflow

The current processing chain is:

ERA5 event download
        │
        ├── large domain
        │
        └── small dense domain
                 │
                 ▼
ERA5 HOD climatology (1991–2020)
                 │
                 ▼
       multi-year HOD means
                 │
                 ▼
          event anomalies
                 │
                 ▼
       diagnostic analysis
                 │
                 ▼
       maps and cross-sections
Repository structure
andean-cold-surge/
├── config/
├── docs/
├── env/
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

Large ERA5 datasets and generated figures are deliberately excluded from version control.

ERA5 / Copernicus CDS configuration

ERA5 data are obtained from the Copernicus Climate Data Store (CDS) using the Python cdsapi client.

A CDS account and local API configuration are required before running the download scripts.

The CDS credentials must be configured outside this repository in:

~/.cdsapirc

The file should contain the API configuration provided by the Copernicus Climate Data Store for the user's account.

Credentials must never be committed to this repository.

The corresponding ERA5 dataset terms and licences must also be accepted through the CDS website before the first download.

Once configured, the connection can be tested with:

python -c "import cdsapi; cdsapi.Client(); print('CDS configuration OK')"
Running an event

Define the central date of the event:

export EVENT_DAYS0="2023-07-17"

Optionally modify the event window:

export PAD_DAYS=2

Then run:

./scripts/run_download_events.sh

By default, data are written under:

data/

An external data directory can instead be specified with:

export COLD_SURGE_BASEDIR=/path/to/era5/data

This is useful when ERA5 data are stored on a large filesystem outside the Git repository.

Building the climatology

Select the months:

export MONTHS="7,8,9"

Download the 1991–2020 hour-of-day climatologies:

./scripts/run_download_climatology.sh

Then construct the multi-year means:

./scripts/run_process_climatology.sh
Computing anomalies

Once both event fields and the corresponding climatological means are available:

./scripts/run_compute_anoms.sh

The resulting anomalies retain the temporal evolution of the event while removing the corresponding 1991–2020 hour-of-day climatological state.

Diagnostic plots

The repository currently includes diagnostics for:

850 hPa temperature and mean sea-level pressure;
850 hPa wind;
700 hPa temperature and geopotential height;
500 hPa temperature and geopotential height;
300 hPa jet and geopotential height;
latitude-height cross-sections;
arbitrary transects across the cold-air structure.

These diagnostics are intended to characterize both the synoptic environment and the vertical structure of the cold-air dome.

Scientific questions

The workflow is designed to address questions including:

What distinguishes quasi-stationary cold-air structures from classical Andean cold surges?
What controls their northward propagation speed?
How important is the opposing low-level background flow?
What role does downstream anticyclonic circulation play in maintaining the cold-air dome?
How shallow is the cold air and how does its depth evolve?
Is horizontal cold advection dominant during the event?
How important are vertical motion and diabatic processes?
Does the disturbance exhibit characteristics consistent with a topographically trapped wave?
Under what synoptic configurations does the cold-air mass remain stationary, propagate northward, or retreat?
Current status

The repository currently provides the ERA5 acquisition, climatology, anomaly, and diagnostic-plotting workflow.

Ongoing development focuses on event comparison and dynamical diagnostics, including the propagation of the cold-air boundary, low-level momentum balance, vertical structure, and the possible role of topographically trapped disturbances along the Andes.

Data availability

ERA5 data are distributed by the Copernicus Climate Change Service.

Raw and processed ERA5 files are not included in this repository because of their size. The download scripts provide the information required to reconstruct the datasets used by the analysis.
