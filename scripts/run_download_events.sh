#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Download ERA5 event windows
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export COLD_SURGE_BASEDIR="${COLD_SURGE_BASEDIR:-${PROJECT_DIR}/data}"

# Día(s) centrales del evento, separados por coma.
export EVENT_DAYS0="${EVENT_DAYS0:-2023-07-17}"

LOG_DIR="${PROJECT_DIR}/logs"
mkdir -p "${LOG_DIR}"

TS=$(date +"%Y%m%d_%H%M%S")

echo "[INFO] Data directory: ${COLD_SURGE_BASEDIR}"
echo "[INFO] Event day(s): ${EVENT_DAYS0}"

echo "[INFO] Downloading large-domain ERA5 event..."
python "${SCRIPT_DIR}/download/download_events_large.py" \
    > "${LOG_DIR}/events_large_${TS}.log" 2>&1

echo "[INFO] Downloading small dense-domain ERA5 event..."
python "${SCRIPT_DIR}/download/download_events_small_dense.py" \
    > "${LOG_DIR}/events_small_dense_${TS}.log" 2>&1

echo "[INFO] Completed."
echo "[INFO] Logs: ${LOG_DIR}"
