#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Build ERA5 HOD multi-year climatologies
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export COLD_SURGE_BASEDIR="${COLD_SURGE_BASEDIR:-${PROJECT_DIR}/data}"
export MONTHS="${MONTHS:-7,8,9}"

LOG_DIR="${PROJECT_DIR}/logs"
mkdir -p "${LOG_DIR}"

TS=$(date +"%Y%m%d_%H%M%S")

echo "[INFO] Building 1991-2020 HOD climatological means."
echo "[INFO] Months: ${MONTHS}"

python "${SCRIPT_DIR}/processing/build_multiyear_means.py" \
    > "${LOG_DIR}/build_multiyear_${TS}.log" 2>&1

echo "[INFO] Completed."
echo "[INFO] Log: ${LOG_DIR}/build_multiyear_${TS}.log"
