'''
This script analyzes historical GeoGlows data for the stations of interest from GRDC.
It tests the initial bias-correction method available in GeoGlows.
It also adds a Quantile Mapping correction from this library:
https://pankajkarman.github.io/bias_correction/bias_correction.html#installation
'''

# Import required libraries
import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import geoglows 
import plotly.graph_objects as go
from bias_correction import BiasCorrection

t0 = datetime.now()

# Set paths for data files
cwd = Path.cwd()
fila_statii = os.path.join(cwd, 'config', 'coords_stations.csv')
data_folder_hist = os.path.join(cwd, 'data_init', 'historical')
data_folder_grdc = os.path.join(cwd,'grdc_obs')
data_folder_forecast = os.path.join(cwd, 'data_init', 'forecast')
data_folder_analiza = os.path.join(cwd, 'analiza', 'analiza_prognoza')
data_benchmark = os.path.join(cwd, 'benchmark')
#start_date = pd.Timestamp('1991-01-01')
#end_date = pd.Timestamp('2020-12-31')

# Ensure export folders exist
Path(data_folder_analiza).mkdir(parents=True, exist_ok=True)
Path(data_benchmark).mkdir(parents=True, exist_ok=True)

# Load the stations of interest
df_stations = pd.read_csv(fila_statii)
names = df_stations['NAME'].tolist()

benchmark_df = pd.DataFrame(columns=['tip', 'durata'])


for name in names:
    # Open and prepare GRDC observed data
    df_grdc = pd.read_csv(os.path.join(data_folder_grdc, f'{name}_Q_Day.csv'))
    df_grdc['date'] = pd.to_datetime(df_grdc['date'])
    df_grdc = df_grdc.dropna(subset=['date']).sort_values('date').set_index('date')
    #df_grdc = df_grdc.loc[start_date:end_date]

    # Open and prepare the GeoGlows historical data
    df_hist = pd.read_csv(os.path.join(data_folder_hist, f'{name}_historical_Q_Daily.csv'))
    df_hist['time'] = pd.to_datetime(df_hist['time'])
    df_hist = df_hist.dropna(subset=['time']).sort_values('time').set_index('time')
    #df_hist = df_hist.loc[start_date:end_date]

    # pastreaza intreg intervalul din GRDC
    df_hist = df_hist.reindex(df_grdc.index)
    # daca vrei doar overlap-ul valid
    common_index = df_grdc.index.intersection(df_hist.index.dropna())
    df_grdc = df_grdc.loc[common_index]
    df_hist = df_hist.loc[common_index]

    # Open and prepare the ensemble and statistics forecast data
    df_ens = pd.read_csv(os.path.join(data_folder_forecast, f'{name}_forecast_ensembles.csv'))
    df_stats = pd.read_csv(os.path.join(data_folder_forecast, f'{name}_forecast_stats.csv'))
    df_ens['time'] = pd.to_datetime(df_ens['time'])
    df_ens.set_index('time', inplace=True)
    df_stats['time'] = pd.to_datetime(df_stats['time'])
    df_stats.set_index('time', inplace=True)

    # acum aplicam functiile de bias correction din geoglows
    df_ens_cr = geoglows.bias.correct_forecast(forecast_data=df_ens, simulated_data=df_hist, observed_data=df_grdc, use_month=0)
    df_stats_cr = geoglows.bias.correct_forecast(forecast_data=df_stats, simulated_data=df_hist, observed_data=df_grdc, use_month=0)

    # Save corrected dataframe
    df_ens_cr.to_csv(os.path.join(data_folder_analiza, f'{name}_forecast_ensembles_gw.csv'))
    df_stats_cr.to_csv(os.path.join(data_folder_analiza, f'{name}_forecast_stats_gw.csv'))

    # Create and save HTML charts
    fig_ens = geoglows.plots.forecast_ensembles(df_ens_cr, plot_type='plotly', plot_titles=[f" {name}"])
    fig_stats = geoglows.plots.forecast_stats(df_stats_cr, plot_type='plotly', plot_titles=[f" {name}"])
    fig_ens.write_html(os.path.join(data_folder_analiza, f'{name}_forecast_ens_gw.html'), include_plotlyjs='cdn')
    fig_stats.write_html(os.path.join(data_folder_analiza, f'{name}_forecast_stats_gw.html'), include_plotlyjs='cdn')

    print(f'Completed analysis for station {name}')

# Quantile Mapping is currently difficult because each forecast column must be processed separately

t1 = datetime.now()
print(f'Duration of forecast analysis and plotting: {t1 - t0}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'analiza_plot', 'durata': t1 - t0}
# saLvam benchmark-ul intr-un fisier csv
benchmark_file = os.path.join(data_benchmark, 'benchmark_06_analiza_prognoza.csv')
benchmark_df.to_csv(benchmark_file, index=False)
print('All data was analyzed and plotted successfully!')
print('FB')