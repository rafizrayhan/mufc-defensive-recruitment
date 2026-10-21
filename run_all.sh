#!/usr/bin/env bash
# Run the full pipeline from data download to final charts.
set -e
cd "$(dirname "$0")/src"
for step in 01_fetch_data 02_build_dataset 03_percentiles 04_united_radars 05_gap_analysis \
            06_other_leagues 07_market_data 08_score_shortlist 09_head_to_head 10_sensitivity 11_fit_vs_value; do
  echo "== $step"
  python "$step.py"
done
