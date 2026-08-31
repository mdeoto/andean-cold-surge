#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Compute event anomalies against HOD climatology
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export COLD_SURGE_BASEDIR="${COLD_SURGE_BASEDIR:-${PROJECT_DIR}/data}"

LOG_DIR="${PROJECT_DIR}/logs"
mkdir -p "${LOG_DIR}"

TS=$(date +"%Y%m%d_%H%M%S")

echo "[INFO] Computing ERA5 anomalies..."

python "${SCRIPT_DIR}/processing/compute_anomalies_events.py" \
    > "${LOG_DIR}/anomalies_${TS}.log" 2>&1

echo "[INFO] Completed."
echo "[INFO] Log: ${LOG_DIR}/anomalies_${TS}.log"
