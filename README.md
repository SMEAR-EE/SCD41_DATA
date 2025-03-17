# SCD41_DATA

## SMEAR Station Dataset Repository

This repository serves as a centralized, automatically-updated dataset repository containing experimental data (SCD41 low-cost CO2 sensor data) collected at the SMEAR station (smear.emu.ee). </br>
This repository periodically auto-synchronizes the dataset from the remote source NAS storage server, preprocesses, and maintains it here for ease of access, reproducibility, and analysis.


## Repository Structure

```
.
├── .github/
│   └── workflows
│       └── data_sync.yml      # GitHub Actions workflow for automation
├── scripts
│   └── manage_csv.sh          # Bash script managing data sync and CSV updates
├── data
│   ├── raw_json               # Directory storing synchronized JSON data files
│   └── data.csv               # Main CSV file containing processed and cleaned data
├── .gitignore
└── README.md                  # Documentation

```

## Data Source and Update Frequency

- The SMEAR station NAS generates JSON data files every 10 minutes (~300KB per 6 months).
- We synchronize the data in this repository bi-weekly.

## Workflow Overview
- **Data Retrieval:** Fetch new JSON files from the NAS using SSH/SCP.
- **Data Processing:** Convert new JSON files to CSV, appending as new rows to the main CSV file.
- **Automation:** Scheduled via GitHub Actions, running bi-weekly.

## Repository Setup
- The synchronization and processing workflow is automated through `.github/workflows/data_sync.yml`.
- Scripts for data management are stored in the `scripts` directory.

## Accessing the Data
Clone this repository and regularly pull updates to have the latest datasets:

```sh
git clone https://github.com/SMEAR-EE/SCD41_DATA.git
cd SCD41_DATA
```

After initial setup, updates are automatically appended to the CSV file (`data/SMEAR_sensor_data.csv`).

## Contributing and Issues
- Report issues or suggest improvements via GitHub Issues.
- Contributions are welcome via Pull Requests.

