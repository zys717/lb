# S001–S020 Scenarios (Basic Layer) – Consolidated Notes

The original per-scenario READMEs were corrupted and removed. Use this file as the single reference for the first 20 basic scenarios.

## Where to look
- **Scenario definitions**: `scenarios/basic/S0xx_*.jsonc` (see index below).
- **LLM validation reports**: `reports/S0xx_LLM_VALIDATION.json`.
- **RAG reports**: `reports_former20rag/S0xx_RAG_REPORT.json` (archived baseline) or `reports/S0xx_RAG_REPORT.json` if regenerated.
- **Ground truth**: `ground_truth/S0xx_*.json` (when provided).
- **Test guides**: `docs/S0xx_TEST_GUIDE.md` (includes AirSim run commands and checklists).

## Notes on status
- These 20 scenarios served as the original baseline; keep them unchanged for regression comparisons.
- Brand: LAE-GPT (legacy references to prior names have been removed).

## Scenario index
- S001 – `S001_geofence_basic.jsonc`
- S002 – `S002_multi_geofence.jsonc`
- S003 – `S003_path_crossing.jsonc`
- S004 – `S004_airport_zones.jsonc`
- S005 – `S005_dynamic_tfr.jsonc`
- S006 – `S006_altitude_limit.jsonc`
- S007 – `S007_zone_altitude_limits.jsonc`
- S008 – `S008_structure_waiver.jsonc`
- S009 – `S009_speed_limit.jsonc`
- S010 – `S010_zone_speed_limits.jsonc`
- S011 – `S011_night_flight.jsonc`
- S012 – `S012_time_window.jsonc`
- S013 – `S013_vlos_requirement.jsonc`
- S014 – `S014_bvlos_waiver.jsonc`
- S015 – `S015_dynamic_nfz_avoidance.jsonc`
- S016 – `S016_realtime_obstacle_avoidance.jsonc`
- S017 – `S017_payload_and_drop_restrictions.jsonc`
- S018 – `S018_multi_drone_coordination.jsonc`
- S019 – `S019_airspace_classification.jsonc`
- S020 – `S020_approval_timeline.jsonc`

## How to run (examples)
```bash
# LLM validation
python scripts/validate_scenario.py scenarios/basic/S001_geofence_basic.jsonc \
  --ground-truth ground_truth/S001_violations.json \
  --output reports/S001_LLM_VALIDATION.json

# (Optional) RAG run for any baseline scenario
python rag/rag_S001-S020/run_rag_batch.py S001 --output-dir reports --no-call
```

If you need richer per-scenario descriptions, refer directly to the JSONC files and the corresponding reports. 
