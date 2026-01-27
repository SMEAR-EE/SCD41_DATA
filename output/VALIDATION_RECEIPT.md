# SMEAR Estonia CO2 Data Validation Receipt

**Generated:** 2026-01-27T13:05:32.592198
**Sensors Directory:** `/home/mbz/Documents/PhD/SCD41_DATA/output/sensors`
**Merged Directory:** `/home/mbz/Documents/PhD/SCD41_DATA/output/merged`
**Year-Month Range:** 2024-09 to 2025-09

---

## Validation Summary

**Status:** ⚠️ PASSED_WITH_WARNINGS (100/105 checks passed)

5 warning(s) to review

---

## Sensor Data Summary

| Sensor | Rows | Coverage | Months | Date Range |
|--------|-----:|:--------:|:------:|------------|
| CO2_SCT1_2M | 54,172 | 98.1% | 13 | 2024-09-12 to 2025-09-30 |
| CO2_30M_A | 22,917 | 43.0% | 12 | 2024-09-19 to 2025-09-24 |
| CO2_30M_B | 18,608 | 35.1% | 12 | 2024-09-19 to 2025-09-22 |
| CO2_30M_C | 44,496 | 87.1% | 12 | 2024-10-02 to 2025-09-21 |
| LGR_30M | 55,969 | 98.4% | 13 | 2024-09-01 to 2025-09-30 |

---

## Reference Comparison (SCD41 2m vs LGR)

Comparison of low-cost SCD41 sensor at 2m against LGR reference at 30m.

| Metric | Value |
|--------|------:|
| Paired observations | 52,858 |
| Bias | +92.1 ppm |
| RMSE | 131.9 ppm |
| MAE | 93.0 ppm |
| Correlation | 0.331 |

---

## 30M Sensor Comparisons (vs LGR)

| Sensor | n | Bias (ppm) | RMSE (ppm) | Correlation |
|--------|--:|----------:|-----------:|------------:|
| 30M-A | 22,425 | +85.0 | 98.0 | 0.099 |
| 30M-B | 18,339 | +141.6 | 171.2 | 0.014 |
| 30M-C | 43,392 | +118.1 | 128.8 | 0.503 |

---

## Verification Checks

Pipeline processing correctness verified through automated checks.

Time gaps are expected given sensor coverage and are marked as warnings (⚠).
Duplicate/invalid timestamps would be critical issues (✗).

| Check | Status | Detail |
|-------|:------:|--------|
| verification:CO2_30M_A | ⚠ | 140 gaps >10min |
| verification:CO2_30M_B | ⚠ | 112 gaps >10min |
| verification:CO2_30M_C | ⚠ | 310 gaps >10min |
| verification:CO2_SCT1_2M | ⚠ | 168 gaps >10min |
| verification:LGR_30M | ⚠ | 4 gaps >10min |

5 warning(s) - time gaps expected given sensor coverage.

---

## File Checksums (SHA256)

```
10093ac1087ddc9cfcf014e850adc60b1e2b0ec7d9ed35f77884fbe1fa76283a  SMEAR_EE_CO2_merged.csv
```

---

## Detailed Check Results

| Check | Status | Message |
|-------|:------:|---------|
| column_names:CO2_30M_A/CO2_30M_A_10min.csv | ✓ | Clean |
| column_names:CO2_30M_B/CO2_30M_B_10min.csv | ✓ | Clean |
| column_names:CO2_30M_C/CO2_30M_C_10min.csv | ✓ | Clean |
| column_names:CO2_SCT1_2M/CO2_SCT1_2M_10min.csv | ✓ | Clean |
| column_names:LGR_30M/LGR_30M_10min.csv | ✓ | Clean |
| file_inventory:CO2_SCT1_2M | ✓ | 13 CSVs, 13 parquets |
| file_inventory:CO2_30M_A | ✓ | 12 CSVs, 12 parquets |
| file_inventory:CO2_30M_B | ✓ | 12 CSVs, 12 parquets |
| file_inventory:CO2_30M_C | ✓ | 12 CSVs, 12 parquets |
| file_inventory:LGR_30M | ✓ | 13 CSVs, 13 parquets |
| parquet:CO2_30M_A/CO2_30M_A_2024_09.parquet | ✓ | 174 rows, 18.4KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2024_10.parquet | ✓ | 2211 rows, 140.3KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2024_11.parquet | ✓ | 2654 rows, 161.9KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2025_01.parquet | ✓ | 2653 rows, 155.3KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2025_02.parquet | ✓ | 931 rows, 64.0KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2025_03.parquet | ✓ | 2925 rows, 194.7KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2025_04.parquet | ✓ | 1995 rows, 133.3KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2025_05.parquet | ✓ | 4360 rows, 272.9KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2025_06.parquet | ✓ | 428 rows, 33.1KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2025_07.parquet | ✓ | 3100 rows, 191.9KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2025_08.parquet | ✓ | 567 rows, 40.7KB, SNAPPY |
| parquet:CO2_30M_A/CO2_30M_A_2025_09.parquet | ✓ | 919 rows, 65.9KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2024_09.parquet | ✓ | 373 rows, 29.8KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2024_10.parquet | ✓ | 1217 rows, 75.4KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2024_11.parquet | ✓ | 2796 rows, 158.6KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2024_12.parquet | ✓ | 1431 rows, 86.9KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2025_01.parquet | ✓ | 2653 rows, 139.7KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2025_02.parquet | ✓ | 931 rows, 60.4KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2025_03.parquet | ✓ | 1665 rows, 112.8KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2025_04.parquet | ✓ | 888 rows, 61.3KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2025_05.parquet | ✓ | 2333 rows, 141.0KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2025_06.parquet | ✓ | 2984 rows, 185.0KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2025_07.parquet | ✓ | 706 rows, 47.0KB, SNAPPY |
| parquet:CO2_30M_B/CO2_30M_B_2025_09.parquet | ✓ | 631 rows, 43.6KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2024_10.parquet | ✓ | 4203 rows, 246.0KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2024_11.parquet | ✓ | 4280 rows, 233.8KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2024_12.parquet | ✓ | 4433 rows, 234.9KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2025_01.parquet | ✓ | 2060 rows, 103.1KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2025_02.parquet | ✓ | 3696 rows, 215.7KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2025_03.parquet | ✓ | 3061 rows, 192.9KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2025_04.parquet | ✓ | 2419 rows, 156.4KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2025_05.parquet | ✓ | 4360 rows, 267.9KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2025_06.parquet | ✓ | 4260 rows, 254.3KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2025_07.parquet | ✓ | 4380 rows, 269.1KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2025_08.parquet | ✓ | 4371 rows, 262.9KB, SNAPPY |
| parquet:CO2_30M_C/CO2_30M_C_2025_09.parquet | ✓ | 2973 rows, 175.7KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2024_09.parquet | ✓ | 2449 rows, 166.2KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2024_10.parquet | ✓ | 4293 rows, 282.2KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2024_11.parquet | ✓ | 4200 rows, 283.6KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2024_12.parquet | ✓ | 4340 rows, 293.0KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2025_01.parquet | ✓ | 4193 rows, 286.5KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2025_02.parquet | ✓ | 4032 rows, 273.9KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2025_03.parquet | ✓ | 4464 rows, 305.1KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2025_04.parquet | ✓ | 4232 rows, 285.4KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2025_05.parquet | ✓ | 4464 rows, 298.5KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2025_06.parquet | ✓ | 4320 rows, 287.1KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2025_07.parquet | ✓ | 4462 rows, 296.1KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2025_08.parquet | ✓ | 4433 rows, 295.1KB, SNAPPY |
| parquet:CO2_SCT1_2M/CO2_SCT1_2M_2025_09.parquet | ✓ | 4290 rows, 286.8KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2024_09.parquet | ✓ | 4320 rows, 1231.3KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2024_10.parquet | ✓ | 4464 rows, 1292.4KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2024_11.parquet | ✓ | 4320 rows, 1244.1KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2024_12.parquet | ✓ | 4464 rows, 1297.5KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2025_01.parquet | ✓ | 4192 rows, 1221.8KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2025_02.parquet | ✓ | 3590 rows, 1030.9KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2025_03.parquet | ✓ | 4464 rows, 1273.8KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2025_04.parquet | ✓ | 4320 rows, 1221.2KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2025_05.parquet | ✓ | 4464 rows, 1275.6KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2025_06.parquet | ✓ | 4320 rows, 1234.3KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2025_07.parquet | ✓ | 4408 rows, 1249.7KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2025_08.parquet | ✓ | 4323 rows, 1226.5KB, SNAPPY |
| parquet:LGR_30M/LGR_30M_2025_09.parquet | ✓ | 4320 rows, 1232.3KB, SNAPPY |
| csv_parquet_match:CO2_SCT1_2M_2024_09 | ✓ | rows: 2449==2449, values: True |
| csv_parquet_match:CO2_SCT1_2M_2024_10 | ✓ | rows: 4293==4293, values: True |
| csv_parquet_match:CO2_SCT1_2M_2024_11 | ✓ | rows: 4200==4200, values: True |
| csv_parquet_match:CO2_SCT1_2M_2024_12 | ✓ | rows: 4340==4340, values: True |
| csv_parquet_match:CO2_SCT1_2M_2025_01 | ✓ | rows: 4193==4193, values: True |
| csv_parquet_match:CO2_SCT1_2M_2025_02 | ✓ | rows: 4032==4032, values: True |
| csv_parquet_match:CO2_SCT1_2M_2025_03 | ✓ | rows: 4464==4464, values: True |
| csv_parquet_match:CO2_SCT1_2M_2025_04 | ✓ | rows: 4232==4232, values: True |
| csv_parquet_match:CO2_SCT1_2M_2025_05 | ✓ | rows: 4464==4464, values: True |
| csv_parquet_match:CO2_SCT1_2M_2025_06 | ✓ | rows: 4320==4320, values: True |
| csv_parquet_match:CO2_SCT1_2M_2025_07 | ✓ | rows: 4462==4462, values: True |
| csv_parquet_match:CO2_SCT1_2M_2025_08 | ✓ | rows: 4433==4433, values: True |
| csv_parquet_match:CO2_SCT1_2M_2025_09 | ✓ | rows: 4290==4290, values: True |
| csv_parquet_match:LGR_30M_2024_09 | ✓ | rows: 4320==4320, values: True |
| csv_parquet_match:LGR_30M_2024_10 | ✓ | rows: 4464==4464, values: True |
| csv_parquet_match:LGR_30M_2024_11 | ✓ | rows: 4320==4320, values: True |
| csv_parquet_match:LGR_30M_2024_12 | ✓ | rows: 4464==4464, values: True |
| csv_parquet_match:LGR_30M_2025_01 | ✓ | rows: 4192==4192, values: True |
| csv_parquet_match:LGR_30M_2025_02 | ✓ | rows: 3590==3590, values: True |
| csv_parquet_match:LGR_30M_2025_03 | ✓ | rows: 4464==4464, values: True |
| csv_parquet_match:LGR_30M_2025_04 | ✓ | rows: 4320==4320, values: True |
| csv_parquet_match:LGR_30M_2025_05 | ✓ | rows: 4464==4464, values: True |
| csv_parquet_match:LGR_30M_2025_06 | ✓ | rows: 4320==4320, values: True |
| csv_parquet_match:LGR_30M_2025_07 | ✓ | rows: 4408==4408, values: True |
| csv_parquet_match:LGR_30M_2025_08 | ✓ | rows: 4323==4323, values: True |
| csv_parquet_match:LGR_30M_2025_09 | ✓ | rows: 4320==4320, values: True |
| merged_data | ✓ | 56,654 rows, 100 columns, 50.5 MB | 2024-09-01 to 2025-09-30 |
| data_quality | ✓ | 2 time gaps >10min, bias=92.1 ppm |
| verification:CO2_30M_A | ✗ | 140 gaps >10min |
| verification:CO2_30M_B | ✗ | 112 gaps >10min |
| verification:CO2_30M_C | ✗ | 310 gaps >10min |
| verification:CO2_SCT1_2M | ✗ | 168 gaps >10min |
| verification:LGR_30M | ✗ | 4 gaps >10min |

---

*Report generated by SMEAR Estonia CO2 Processing Pipeline*