'''
This script downloads historical data from GeoGlows for the stations of interest from GRDC.
Queries use the station LINKNO, and the data is initially downloaded in Zarr format.
For comparison, the data downloaded through the GeoGlows API is also saved to compare download times.
'''

# Import required libraries
import os
import xarray as xr
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import geoglows 

t0 = datetime.now()

# Set paths for data files
cwd = Path.cwd()
fila_statii = os.path.join(cwd, 'config', 'coords_stations.csv')
data_folder_hist = os.path.join(cwd, 'data_init', 'historical')
data_benchmark = os.path.join(cwd, 'benchmark')

# Ensure the export folder exists
Path(data_folder_hist).mkdir(parents=True, exist_ok=True)
Path(data_benchmark).mkdir(parents=True, exist_ok=True)

# Load the stations of interest
df_stations = pd.read_csv(fila_statii)
reachs = df_stations['LINKNO'].tolist()
names = df_stations['NAME'].tolist()
benchmark_df = pd.DataFrame(columns=['tip', 'durata'])

# DOWNLOAD DIRECTLY FROM AWS S3 WITHOUT USING THE GEOGLOWS API
t1 = datetime.now()
# Download historical GeoGlows data for the stations of interest
# Hourly data
retro_hourly_zarr_uri = 's3://geoglows-v2/retrospective/hourly.zarr'
ds = xr.open_dataset(retro_hourly_zarr_uri, engine='zarr', storage_options={'anon': True})

# Load one dataframe containing all stations
# The result has a multi-index: river_id + timestamp, and column Q contains discharge
# Then extract each station and save it separately
all_hist_df = ds.sel(river_id=reachs)["Q"].to_dataframe()

for reach in reachs:
    station_df = all_hist_df.xs(reach, level='river_id', drop_level=True)
    if isinstance(station_df, pd.Series):
        station_df = station_df.to_frame(name='Q')

    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Hourly.csv')
    station_df.to_csv(output_filename, index=True)
    print(f'Hourly historical data for station {locname} was saved to: {output_filename}')

t2 = datetime.now()
print(f'Hourly historical data download duration: {t2 - t1}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_hourly_aws', 'durata': t2 - t1}

# Apply the same logic to daily historical data
retro_daily_zarr_uri = 's3://geoglows-v2/retrospective/daily.zarr'
ds = xr.open_dataset(retro_daily_zarr_uri, engine='zarr', storage_options={'anon': True})
all_hist_df = ds.sel(river_id=reachs)["Q"].to_dataframe()

for reach in reachs:
    station_df = all_hist_df.xs(reach, level='river_id', drop_level=True)
    if isinstance(station_df, pd.Series):
        station_df = station_df.to_frame(name='Q')

    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Daily.csv')
    station_df.to_csv(output_filename, index=True)
    print(f'Daily historical data for station {locname} was saved to: {output_filename}')

t3 = datetime.now()
print(f'Daily historical data download duration: {t3 - t2}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_daily_aws', 'durata': t3 - t2}

# Apply the same logic to monthly historical data
retro_monthly_zarr_uri = 's3://geoglows-v2/retrospective/monthly-timeseries.zarr'
ds = xr.open_dataset(retro_monthly_zarr_uri, engine='zarr', storage_options={'anon': True})
all_hist_df = ds.sel(river_id=reachs)["Q"].to_dataframe()

for reach in reachs:
    station_df = all_hist_df.xs(reach, level='river_id', drop_level=True)
    if isinstance(station_df, pd.Series):
        station_df = station_df.to_frame(name='Q')

    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Monthly.csv')
    station_df.to_csv(output_filename, index=True)
    print(f'Monthly historical data for station {locname} was saved to: {output_filename}')

t4 = datetime.now()
print(f'Monthly historical data download duration: {t4 - t3}')
print(f'Total direct AWS historical data download duration: {t4 - t1}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_monthly_aws', 'durata': t4 - t3}
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_total_aws', 'durata': t4 - t1}

# DOWNLOAD FROM THE GEOGLOWS API TOO, FOR COMPARISON
# Download historical GeoGlows data for the stations of interest
# Hourly data
t5 = datetime.now() 
all_hist_df_api = geoglows.data.retrospective(river_id=reachs, format='df', resolution='hourly')
coloane = all_hist_df_api.columns.tolist()

for coloana in coloane:
    reach = int(coloana)
    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Hourly_API.csv')
    all_hist_df_api[[coloana]].to_csv(output_filename, index=True)
    print(f'Hourly historical data for station {locname} was saved to: {output_filename}')

t6 = datetime.now()
print(f'Hourly historical API download duration: {t6 - t5}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_hourly_api', 'durata': t6 - t5}

# Apply the same logic to daily historical data
t7 = datetime.now() 
all_hist_df_api = geoglows.data.retrospective(river_id=reachs, format='df', resolution='daily')
coloane = all_hist_df_api.columns.tolist()

for coloana in coloane:
    reach = int(coloana)
    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Daily_API.csv')
    all_hist_df_api[[coloana]].to_csv(output_filename, index=True)
    print(f'Daily historical data for station {locname} was saved to: {output_filename}')

t8 = datetime.now()
print(f'Daily historical API download duration: {t8 - t7}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_daily_api', 'durata': t8 - t7}

# Apply the same logic to monthly historical data
t9 = datetime.now()
all_hist_df_api = geoglows.data.retrospective(river_id=reachs, format='df', resolution='monthly')
coloane = all_hist_df_api.columns.tolist()      

for coloana in coloane:
    reach = int(coloana)
    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Monthly_API.csv')
    all_hist_df_api[[coloana]].to_csv(output_filename, index=True)
    print(f'Monthly historical data for station {locname} was saved to: {output_filename}')

t10 = datetime.now()
print(f'Monthly historical API download duration: {t10 - t9}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_monthly_api', 'durata': t10 - t9}
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_total_api', 'durata': t10 - t5}

print(f'Total historical API download duration: {t10 - t5}')
print(f'Total historical data download duration: {t10 - t1}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_total_script', 'durata': t10 - t0}

benchmark_file = os.path.join(data_benchmark, 'benchmark_historical.csv')
benchmark_df.to_csv(benchmark_file, index=False)
print('All historical data was downloaded successfully!')
print('FB')