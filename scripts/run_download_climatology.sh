#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Download ERA5 hour-of-day climatologies
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export COLD_SURGE_BASEDIR="${COLD_SURGE_BASEDIR:-${PROJECT_DIR}/data}"

# Comma-separated months.
export MONTHS="${MONTHS:-7,8,9}"

LOG_DIR="${PROJECT_DIR}/logs"
mkdir -p "${LOG_DIR}"

TS=$(date +"%Y%m%d_%H%M%S")

echo "[INFO] Data directory: ${COLD_SURGE_BASEDIR}"
echo "[INFO] Months: ${MONTHS}"

echo "[INFO] Starting large-domain HOD climatology..."
nohup python "${SCRIPT_DIR}/download/download_climatology_hod_large.py" \
    > "${LOG_DIR}/clim_hod_large_${TS}.log" 2>&1 &

PID_LARGE=$!

echo "[INFO] Starting small dense-domain HOD climatology..."
nohup python "${SCRIPT_DIR}/download/download_climatology_hod_small_dense.py" \
    > "${LOG_DIR}/clim_hod_small_dense_${TS}.log" 2>&1 &

PID_SMALL=$!

echo "[INFO] Processes launched:"
echo "       large PID: ${PID_LARGE}"
echo "       small PID: ${PID_SMALL}"
echo
echo "Follow logs with:"
echo "  tail -f ${LOG_DIR}/clim_hod_large_${TS}.log"
echo "  tail -f ${LOG_DIR}/clim_hod_small_dense_${TS}.log"
