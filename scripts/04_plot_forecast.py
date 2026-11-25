'''
This script plots forecast data from GeoGlows for the stations of interest from GRDC.
It tests plotting time: first, it plots during download, then it reads and plots the CSV files. Plotting times are compared.
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
data_folder_plot = os.path.join(cwd, 'data_init', 'plot_forecast')
data_benchmark = os.path.join(cwd, 'benchmark')

# Ensure the export folders exist
Path(data_folder_fcst).mkdir(parents=True, exist_ok=True)
Path(data_folder_plot).mkdir(parents=True, exist_ok=True)
Path(data_benchmark).mkdir(parents=True, exist_ok=True)

# Load the stations of interest
df_stations = pd.read_csv(fila_statii)
reachs = df_stations['LINKNO'].tolist()
names = df_stations['NAME'].tolist()

benchmark_df = pd.DataFrame(columns=['tip', 'durata'])

# Download all data with the GeoGlows API, then split it
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

    # Plot forecast data for the current station
    fig_s = geoglows.plots.forecast_stats(station_df_s, plot_type='plotly', plot_titles=[f" {locname}"])
    fig_s.write_html(os.path.join(data_folder_plot, f'{locname}_forecast_stats.html'), include_plotlyjs='cdn')
    # include_plotlyjs='cdn' avoids embedding the Plotly library in the HTML file;
    # the library is loaded from a Content Delivery Network so the HTML file is smaller and loads faster
    station_df_e.set_index('time', inplace=True)
    fig_e = geoglows.plots.forecast_ensembles(station_df_e, plot_type='plotly', plot_titles=[f" {locname}"])
    fig_e.write_html(os.path.join(data_folder_plot, f'{locname}_forecast_ensembles.html'), include_plotlyjs='cdn')  

    print(f'Forecast statistics for station {locname} were saved to: {output_filename_s}')
    print(f'Forecast ensembles for station {locname} were saved to: {output_filename_e}')
    print("Forecast charts were generated and saved for station:", locname)

t2 = datetime.now()
print(f'Duration of batched forecast API download and plotting: {t2 - t1}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'forecast_plot_all_api', 'durata': t2 - t1}

# Now open and plot the CSV files only
t3 = datetime.now()

# List CSV files in data_init/forecast
csv_files_s = [f for f in os.listdir(data_folder_fcst) if f.endswith('stats_individual.csv')]
csv_files_e = [f for f in os.listdir(data_folder_fcst) if f.endswith('ensembles_individual.csv')]

for csv_file_s, csv_file_e in zip(csv_files_s, csv_files_e):
    locname = csv_file_s.split('_forecast_stats_individual.csv')[0]
    station_df_s = pd.read_csv(os.path.join(data_folder_fcst, csv_file_s), index_col=0)
    station_df_e = pd.read_csv(os.path.join(data_folder_fcst, csv_file_e), index_col=0)
    station_df_s.index = pd.to_datetime(station_df_s.index, utc=True)
    station_df_e.index = pd.to_datetime(station_df_e.index, utc=True) 

    # Plot forecast data for the current station
    fig_s = geoglows.plots.forecast_stats(station_df_s, plot_type='plotly', plot_titles=[f" {locname}"])
    fig_s.write_html(os.path.join(data_folder_plot, f'{locname}_forecast_stats_from_csv.html'), include_plotlyjs='cdn')
    fig_e = geoglows.plots.forecast_ensembles(station_df_e, plot_type='plotly', plot_titles=[f" {locname}"])
    fig_e.write_html(os.path.join(data_folder_plot, f'{locname}_forecast_ensembles_from_csv.html'), include_plotlyjs='cdn')  
    print("Forecast charts were generated and saved for station:", locname)

t4 = datetime.now()
print(f'Duration of plotting forecast data from CSV files: {t4 - t3}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'forecast_plot_from_csv', 'durata': t4 - t3}
benchmark_df.loc[len(benchmark_df)] = {'tip': f'forecast_total_plot', 'durata': t4 - t0}

# Save the benchmark to a CSV file
benchmark_file = os.path.join(data_benchmark, 'benchmark_ploting.csv')
benchmark_df.to_csv(benchmark_file, index=False)
print('All forecast data was downloaded and plotted successfully!')
print('FB')

