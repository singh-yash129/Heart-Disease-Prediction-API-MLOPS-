#!/usr/bin/env bash
# stress_test.sh — Deliverable 6: wrk stress test with >2000 concurrent connections
# Usage: bash scripts/stress_test.sh <EXTERNAL_IP>
set -e

# Raise open file descriptor limit for 2100 concurrent sockets
ulimit -n 65535 2>/dev/null || ulimit -n 4096 2>/dev/null || true

EXTERNAL_IP="${1:-localhost:8080}"
URL="http://${EXTERNAL_IP}/predict"
THREADS=4
CONNECTIONS=2100      # >2000 as required
DURATION=30s
LUA_SCRIPT="src/stress_test.lua"
RESULTS_FILE="reports/stress_test_results.txt"

echo "======================================================"
echo "  Heart Disease API — wrk Stress Test"
echo "======================================================"
echo "  Target URL  : ${URL}"
echo "  Threads     : ${THREADS}"
echo "  Connections : ${CONNECTIONS} (>2000 ✓)"
echo "  Duration    : ${DURATION}"
echo "  Lua Script  : ${LUA_SCRIPT}"
echo "======================================================"
echo ""

# Run wrk and capture output
wrk -t${THREADS} -c${CONNECTIONS} -d${DURATION} \
    -s "${LUA_SCRIPT}" \
    "${URL}" 2>&1 | tee "${RESULTS_FILE}"

echo ""
echo "✅ Stress test complete. Results saved → ${RESULTS_FILE}"
echo ""
echo "📊 To view GCP Cloud Monitoring metrics:"
echo "   https://console.cloud.google.com/monitoring/dashboards"
