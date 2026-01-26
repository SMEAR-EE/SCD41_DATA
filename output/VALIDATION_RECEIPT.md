# SMEAR Estonia CO2 Data Validation Receipt

**Generated:** 2026-01-26T16:25:36.677320
**Individual Directory:** ``
**Parquet Directory:** `/home/mbz/Documents/PhD/SCD41_DATA/output/individual/parquet`
**Merged Directory:** ``
**Year-Month Range:** 2024-09 to 2025-06

---

## Validation Summary

**Status:** ✅ PASSED (80/80 checks passed)

All checks passed

---

## Sensor Data Summary

| Sensor | Rows | Coverage | Months | Date Range |
|--------|-----:|:--------:|:------:|------------|
| CO2_SCT1_2M | 40,987 | 97.6% | 10 | 2024-09-12 to 2025-06-30 |
| CO2_30M_A | 18,331 | 49.4% | 9 | 2024-09-19 to 2025-06-03 |
| CO2_30M_B | 17,271 | 43.5% | 10 | 2024-09-19 to 2025-06-21 |
| CO2_30M_C | 32,772 | 83.8% | 9 | 2024-10-02 to 2025-06-30 |
| LGR_30M | 42,918 | 98.4% | 10 | 2024-09-01 to 2025-06-30 |

---

## Reference Comparison (SCD41 2m vs LGR)

Comparison of low-cost SCD41 sensor at 2m against LGR reference at 30m.

| Metric | Value |
|--------|------:|
| Paired observations | 27,057 |
| Bias | +98.3 ppm |
| RMSE | 150.3 ppm |
| MAE | 99.6 ppm |
| Correlation | 0.313 |

---

## 30M Sensor Comparisons (vs LGR)

| Sensor | n | Bias (ppm) | RMSE (ppm) | Correlation |
|--------|--:|----------:|-----------:|------------:|
| 30M-A | 11,334 | +84.2 | 101.8 | -0.151 |
| 30M-B | 10,849 | +118.2 | 160.5 | -0.273 |
| 30M-C | 21,059 | +115.2 | 131.3 | 0.503 |

---

## File Checksums (SHA256)

```
c23913c2517c9eeb335ed21aadd5d444057fff899541e42aafaf9a563e2e454b  SMEAR_EE_CO2_merged.csv
```

---

## Detailed Check Results

| Check | Status | Message |
|-------|:------:|---------|
| column_names:CO2_30M_A_10min.csv | ✓ | Clean |
| column_names:CO2_30M_B_10min.csv | ✓ | Clean |
| column_names:CO2_30M_C_10min.csv | ✓ | Clean |
| column_names:CO2_SCT1_2M_10min.csv | ✓ | Clean |
| column_names:LGR_30M_10min.csv | ✓ | Clean |
| file_inventory:CO2_SCT1_2M | ✓ | 10 CSVs, 10 parquets |
| file_inventory:CO2_30M_A | ✓ | 9 CSVs, 9 parquets |
| file_inventory:CO2_30M_B | ✓ | 10 CSVs, 10 parquets |
| file_inventory:CO2_30M_C | ✓ | 9 CSVs, 9 parquets |
| file_inventory:LGR_30M | ✓ | 10 CSVs, 10 parquets |
| parquet:CO2_30M_A_2024_09.parquet | ✓ | 174 rows, 18.4KB, SNAPPY |
| parquet:CO2_30M_A_2024_10.parquet | ✓ | 2211 rows, 140.3KB, SNAPPY |
| parquet:CO2_30M_A_2024_11.parquet | ✓ | 2654 rows, 161.9KB, SNAPPY |
| parquet:CO2_30M_A_2025_01.parquet | ✓ | 2653 rows, 155.3KB, SNAPPY |
| parquet:CO2_30M_A_2025_02.parquet | ✓ | 931 rows, 64.0KB, SNAPPY |
| parquet:CO2_30M_A_2025_03.parquet | ✓ | 2925 rows, 194.7KB, SNAPPY |
| parquet:CO2_30M_A_2025_04.parquet | ✓ | 1995 rows, 133.3KB, SNAPPY |
| parquet:CO2_30M_A_2025_05.parquet | ✓ | 4360 rows, 272.9KB, SNAPPY |
| parquet:CO2_30M_A_2025_06.parquet | ✓ | 428 rows, 33.1KB, SNAPPY |
| parquet:CO2_30M_B_2024_09.parquet | ✓ | 373 rows, 29.8KB, SNAPPY |
| parquet:CO2_30M_B_2024_10.parquet | ✓ | 1217 rows, 75.4KB, SNAPPY |
| parquet:CO2_30M_B_2024_11.parquet | ✓ | 2796 rows, 158.6KB, SNAPPY |
| parquet:CO2_30M_B_2024_12.parquet | ✓ | 1431 rows, 86.9KB, SNAPPY |
| parquet:CO2_30M_B_2025_01.parquet | ✓ | 2653 rows, 139.7KB, SNAPPY |
| parquet:CO2_30M_B_2025_02.parquet | ✓ | 931 rows, 60.4KB, SNAPPY |
| parquet:CO2_30M_B_2025_03.parquet | ✓ | 1665 rows, 112.8KB, SNAPPY |
| parquet:CO2_30M_B_2025_04.parquet | ✓ | 888 rows, 61.3KB, SNAPPY |
| parquet:CO2_30M_B_2025_05.parquet | ✓ | 2333 rows, 141.0KB, SNAPPY |
| parquet:CO2_30M_B_2025_06.parquet | ✓ | 2984 rows, 185.0KB, SNAPPY |
| parquet:CO2_30M_C_2024_10.parquet | ✓ | 4203 rows, 246.0KB, SNAPPY |
| parquet:CO2_30M_C_2024_11.parquet | ✓ | 4280 rows, 233.8KB, SNAPPY |
| parquet:CO2_30M_C_2024_12.parquet | ✓ | 4433 rows, 234.9KB, SNAPPY |
| parquet:CO2_30M_C_2025_01.parquet | ✓ | 2060 rows, 103.1KB, SNAPPY |
| parquet:CO2_30M_C_2025_02.parquet | ✓ | 3696 rows, 215.7KB, SNAPPY |
| parquet:CO2_30M_C_2025_03.parquet | ✓ | 3061 rows, 192.9KB, SNAPPY |
| parquet:CO2_30M_C_2025_04.parquet | ✓ | 2419 rows, 156.4KB, SNAPPY |
| parquet:CO2_30M_C_2025_05.parquet | ✓ | 4360 rows, 267.9KB, SNAPPY |
| parquet:CO2_30M_C_2025_06.parquet | ✓ | 4260 rows, 254.3KB, SNAPPY |
| parquet:CO2_SCT1_2M_2024_09.parquet | ✓ | 2449 rows, 166.2KB, SNAPPY |
| parquet:CO2_SCT1_2M_2024_10.parquet | ✓ | 4293 rows, 282.2KB, SNAPPY |
| parquet:CO2_SCT1_2M_2024_11.parquet | ✓ | 4200 rows, 283.6KB, SNAPPY |
| parquet:CO2_SCT1_2M_2024_12.parquet | ✓ | 4340 rows, 293.0KB, SNAPPY |
| parquet:CO2_SCT1_2M_2025_01.parquet | ✓ | 4193 rows, 286.5KB, SNAPPY |
| parquet:CO2_SCT1_2M_2025_02.parquet | ✓ | 4032 rows, 273.9KB, SNAPPY |
| parquet:CO2_SCT1_2M_2025_03.parquet | ✓ | 4464 rows, 305.1KB, SNAPPY |
| parquet:CO2_SCT1_2M_2025_04.parquet | ✓ | 4232 rows, 285.4KB, SNAPPY |
| parquet:CO2_SCT1_2M_2025_05.parquet | ✓ | 4464 rows, 298.5KB, SNAPPY |
| parquet:CO2_SCT1_2M_2025_06.parquet | ✓ | 4320 rows, 287.1KB, SNAPPY |
| parquet:LGR_30M_2024_09.parquet | ✓ | 4320 rows, 1231.3KB, SNAPPY |
| parquet:LGR_30M_2024_10.parquet | ✓ | 4464 rows, 1292.4KB, SNAPPY |
| parquet:LGR_30M_2024_11.parquet | ✓ | 4320 rows, 1244.1KB, SNAPPY |
| parquet:LGR_30M_2024_12.parquet | ✓ | 4464 rows, 1297.5KB, SNAPPY |
| parquet:LGR_30M_2025_01.parquet | ✓ | 4192 rows, 1221.8KB, SNAPPY |
| parquet:LGR_30M_2025_02.parquet | ✓ | 3590 rows, 1030.9KB, SNAPPY |
| parquet:LGR_30M_2025_03.parquet | ✓ | 4464 rows, 1273.8KB, SNAPPY |
| parquet:LGR_30M_2025_04.parquet | ✓ | 4320 rows, 1221.2KB, SNAPPY |
| parquet:LGR_30M_2025_05.parquet | ✓ | 4464 rows, 1275.6KB, SNAPPY |
| parquet:LGR_30M_2025_06.parquet | ✓ | 4320 rows, 1234.3KB, SNAPPY |
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
| merged_data | ✓ | 30,303 rows, 100 columns, 26.5 MB | 2024-09-01 to 2025-03-31 |
| data_quality | ✓ | 1 time gaps >10min, bias=98.3 ppm |

---

*Report generated by SMEAR Estonia CO2 Processing Pipeline*