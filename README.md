# gaf

The `gaf` project downloads, processes, compares, and visualizes GRDC observed flows and GeoGlows hydrological data for stations in Romania. It includes retrospective historical data, forecasts, bias corrections, validation, and benchmarks. Results are saved primarily as CSV files and interactive Plotly HTML charts.

The platform is available at [GeoGlows RFS](https://apps.geoglows.org/rfs#lon=25.00&lat=46.00&zoom=7.00&definition=Romania). For platform usage, see the [GeoGlows RFS v2 webinar](https://training.geoglows.org/webinars/rfs-v2-webinar-4/).

## Requirements and installation

- Python 3.12
- Conda or Miniconda
- Internet access for GeoGlows and AWS S3 downloads

The environment is described in `environment.yml` and includes GeoGlows, `bias_correction`, `python-kaleido`, and their dependencies.

From the project root, create and activate the environment:

```powershell
conda env create -f environment.yml
conda activate gaf
```

To update an existing environment:

```powershell
conda env update -f environment.yml --prune
```

Run the scripts from the project root, for example:

```powershell
python scripts\02_download_historical.py
```

## Project structure

```text
gaf/
├── config/
│   └── coords_stations.csv
├── grdc_obs/                 # GRDC .txt sources and observed CSV/PNG series
├── data_init/
│   ├── historical/           # hourly, daily, and monthly GeoGlows series
│   ├── forecast/             # forecast statistics and ensembles
│   ├── plot_historical/
│   └── plot_forecast/        # forecast HTML charts
├── analiza/
│   ├── analiza_istorica/
│   ├── analiza_prognoza/
│   ├── analiza_histograma/
│   ├── analiza_histograma_personalizat/
│   ├── analiza_histograma_personalizat_sqm/
│   ├── validare_prognoza/
│   └── validare_histograma/
├── benchmark/                # download, analysis, and plotting timings
├── scripts/                  # scripts 01–12
├── environment.yml
├── README.md
└── LICENSE
```

The `analiza/` directory also contains directories with saved results for earlier periods or runs, such as `analiza_histograma_1961_1990/`, `analiza_histograma_1991_2020/`, and `analiza_istorica_toti_anii/`. Scripts 07–10 currently use the period 1991-01-01–2020-12-31; the names of older result directories do not change the periods configured in the scripts.

## Station and GRDC data configuration

`config/coords_stations.csv` is the station list used by the download and analysis scripts. It must contain the `NAME` and `LINKNO` columns; the current configuration also includes `LON`, `LAT`, `Area_kmp`, `GRDC_ID`, and `Rau`. `NAME` is used to name files, while `LINKNO` identifies the GeoGlows river.

GRDC data is stored in `grdc_obs/`:

- Original source: `<GRDC_ID>_Q_Day.Cmd.txt`;
- Processed series: `<NAME>_Q_Day.csv`, with the date and discharge columns used by the analyses.

Script `01_aranjare_plotare_date_grdc.py` reads a `.Cmd.txt` source, extracts the metadata and daily series, and saves the CSV and PNG chart. In the script, the source ID is set through the `grdc_nr` variable; change this value to process another station. Processed GRDC files for the project stations are already present in `grdc_obs/`.

## Scripts

All scripts are located in `scripts/` and run with the `gaf` environment active.

| Script | Role and results |
| --- | --- |
| `01_aranjare_plotare_date_grdc.py` | Processes a GRDC `.Cmd.txt` source and saves the observed CSV series and PNG chart in `grdc_obs/`. The GRDC ID is selected in the script through `grdc_nr`. |
| `02_download_historical.py` | Downloads hourly, daily, and monthly retrospective GeoGlows series for configured stations. Compares AWS Zarr downloads with the GeoGlows API and writes files to `data_init/historical/` and timings to `benchmark/benchmark_historical.csv`. |
| `03_download_forecast.py` | Downloads statistics and ensembles for the current date, using both batched and per-station queries. Saves CSV files in `data_init/forecast/` and timings in `benchmark/benchmark_forecast.csv`. |
| `04_plot_forecast.py` | Generates HTML charts for API forecasts and individual CSV files. Saves charts in `data_init/plot_forecast/` and timings in `benchmark/benchmark_ploting.csv`. |
| `05_analiza_istorica.py` | Compares GRDC observations with GeoGlows history for 1991–2020. Applies GeoGlows correction and Basic Quantile Mapping, saves CSV series, HTML tables, and charts in `analiza/analiza_istorica/`, and logs duration in `benchmark_05_analiza_istorica.csv`. |
| `06_analiza_prognoza.py` | Corrects forecast statistics and ensembles with `geoglows.bias.correct_forecast`, using GRDC observations and common historical data. Saves CSV files and charts in `analiza/analiza_prognoza/` and logs duration in `benchmark_06_analiza_prognoza.csv`. |
| `07_analiza_histograma.py` | Compares GRDC/GeoGlows distributions and series before and after Basic Quantile Mapping for 1991–2020. Includes histograms, quantiles, NSE, PBIAS, and KGE-2012; saves `_histograma_bqm.html` files in `analiza/analiza_histograma/`. |
| `08_analiza_histograma_sqm.py` | Same analysis as script 07, using GeoGlows Monthly Quantile Mapping; saves `_histograma_sqm.html` files in `analiza/analiza_histograma/`. |
| `09_analiza_histograma_personalizat.py` | Interactive Basic Quantile Mapping variant. Zooming the time series or entering a custom interval updates the series, histograms, quantiles, and metrics; saves output in `analiza/analiza_histograma_personalizat/`. |
| `10_analiza_histograma_personalizat_sqm.py` | Interactive Monthly Quantile Mapping variant with the same interval updates as script 09; reuses the SQM calculation and chart from script 08. Saves output in `analiza/analiza_histograma_personalizat_sqm/`. |
| `11_validare_prognoza.py` | Uses 1985–1990 GeoGlows history as the validation period and 1991–2020 GRDC and GeoGlows data for calibration. Applies Monthly Quantile Mapping month by month and saves the corrected series and chart in `analiza/validare_prognoza/`; writes `benchmark_11_validare_prognoza.csv`. |
| `12_validare_histograma_sqm.py` | Compares GRDC observations, GeoGlows history, and the corrected 1985–1990 validation series using time series, histograms, quantiles, and metrics. Reads script 11 output and saves charts in `analiza/validare_histograma/`. |

## Workflows

### Historical analysis and current forecast

1. Check the stations in `config/coords_stations.csv` and GRDC files in `grdc_obs/`.
2. If needed, process the GRDC sources with script 01, selecting the ID in `grdc_nr`.
3. Download history with script 02.
4. To analyze the current forecast, download data with script 03 and generate charts with script 04.
5. Run script 05 for historical analysis and/or script 06 for the current forecast.

### Distribution analysis and Monthly Quantile Mapping

- Run script 07 for Basic Quantile Mapping or script 08 for Monthly Quantile Mapping.
- Run script 09 for interactive Basic QM analysis or script 10 for interactive Monthly QM analysis. These scripts read the GRDC series and daily GeoGlows history directly.

### Historical-period validation

1. Run script 02 to obtain the retrospective daily GeoGlows series.
2. Run script 11 to apply Monthly Quantile Mapping correction for 1985–1990, calibrated on 1991–2020.
3. Run script 12 to generate comparative charts for the validation period.

## Benchmark files

The scripts save timing measurements in the following files in `benchmark/`:

- `benchmark_historical.csv` — AWS/API historical download comparison;
- `benchmark_forecast.csv` — forecast download;
- `benchmark_ploting.csv` — forecast chart generation;
- `benchmark_05_analiza_istorica.csv` and `benchmark_06_analiza_prognoza.csv` — historical and forecast analyses;
- `benchmark_11_validare_prognoza.csv` — historical-period validation.

## Notes

- The scripts use `config/coords_stations.csv` for analyzed stations and rely on corresponding input files in `grdc_obs/`, `data_init/historical/`, and `data_init/forecast/`.
- Download scripts require an internet connection and may request GeoGlows data for the current date.
- Scripts 07–10 use the 1991–2020 period; scripts 11–12 use the 1985–1990 validation period and the 1991–2020 calibration period.
- Plotly HTML files may load the Plotly library from a CDN, so viewing them may require an internet connection.
- The project is distributed under the MIT license; details are in `LICENSE`.
