'''
This script downloads forecast data from GeoGlows for the stations of interest from GRDC.
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
data_folder_fcst = os.path.join(cwd, 'data_init', 'forecast')
data_benchmark = os.path.join(cwd, 'benchmark')

# Ensure the export folders exist
Path(data_folder_fcst).mkdir(parents=True, exist_ok=True)
Path(data_benchmark).mkdir(parents=True, exist_ok=True)

# Load the stations of interest
df_stations = pd.read_csv(fila_statii)
reachs = df_stations['LINKNO'].tolist()
names = df_stations['NAME'].tolist()

benchmark_df = pd.DataFrame(columns=['tip', 'durata'])

# DOWNLOAD IS DIFFICULT FROM AWS S3 BECAUSE THE DAILY LINK MUST BE CONSTRUCTED
# Therefore, the GeoGlows API is used for the download
t1 = datetime.now()
data = t1.strftime('%Y%m%d')
# It may be necessary to go back one day
# data = (t1 - timedelta(days=1)).strftime('%Y%m%d') # Uncomment this line if the current-day forecast download problem is resolved

all_stats_xr = geoglows.data.forecast_stats(river_id=reachs, date=data, data_source='aws', format='xarray' )
all_ens_df = geoglows.data.forecast_ensembles(river_id=reachs, date=data, data_source='aws', format='df' )
flat_ens_df = all_ens_df.reset_index()

for i in range(len(reachs)):
    reach = reachs[i]
    locname = names[i].replace(' ', '_')
    station_df_s = all_stats_xr.sel(river_id=reach).to_dataframe()
    station_df_s = station_df_s.drop(columns=['river_id'])
    output_filename_s = os.path.join(data_folder_fcst, f'{locname}_forecast_stats.csv')
    station_df_s.to_csv(output_filename_s, index=True)

    station_df_e = flat_ens_df[flat_ens_df.loc[:, 'river_id']==reach] 
    station_df_e = station_df_e.drop(columns=['river_id'])
    output_filename_e = os.path.join(data_folder_fcst, f'{locname}_forecast_ensembles.csv')
    station_df_e.to_csv(output_filename_e, index=False)
    print(f'Forecast statistics for station {locname} were saved to: {output_filename_s}')
    print(f'Forecast ensembles for station {locname} were saved to: {output_filename_e}')

t2 = datetime.now()
print(f'Duration of batched forecast API download: {t2 - t1}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'forecast_all_api', 'durata': t2 - t1}

t3 = datetime.now()
# Now loop through the API and query each station separately
for i in range(len(reachs)):
    reach = reachs[i]
    locname = names[i].replace(' ', '_')
    stats_df = geoglows.data.forecast_stats(river_id=reach, date=data, data_source='aws', format='df' )
    ens_df = geoglows.data.forecast_ensembles(river_id=reach, date=data, data_source='aws', format='df' )
    # Save both types of data to CSV files
    output_filename_s = os.path.join(data_folder_fcst, f'{locname}_forecast_stats_individual.csv')
    stats_df.to_csv(output_filename_s, index=True)
    output_filename_e = os.path.join(data_folder_fcst, f'{locname}_forecast_ensembles_individual.csv')
    ens_df.to_csv(output_filename_e, index=True)
    print(f'Forecast statistics for station {locname} were saved to: {output_filename_s}')
    print(f'Forecast ensembles for station {locname} were saved to: {output_filename_e}')

t4 = datetime.now()
print(f'Duration of individual forecast API download: {t4 - t3}')
benchmark_df.loc[len(benchmark_df)] = {'tip': f'forecast_individual_api', 'durata': t4 - t3}
# adaugare timp total la interogari 
benchmark_df.loc[len(benchmark_df)] = {'tip': f'forecast_total_api', 'durata': t4 - t1}
# adaugare timp total pe tot scriptul
benchmark_df.loc[len(benchmark_df)] = {'tip': f'forecast_total_script', 'durata': t4 - t0}  

# Save the benchmark to a CSV file
benchmark_file = os.path.join(data_benchmark, 'benchmark_forecast.csv')
benchmark_df.to_csv(benchmark_file, index=False)
print('All forecast data was downloaded successfully!')
print('FB')

