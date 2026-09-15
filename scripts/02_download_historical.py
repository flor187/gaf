'''
Acest script are rolul de a descarca datele istorice de la geogglows pentru statiile de interes de la GRDC.
Interogarea se face pe baza id-ului LINKNO al statiei, iar datele sunt descarcate initial in format zarr.
Ulterior pentru comparatie salvam si datele descarcate prin API-ul geoglows, pentru a vedea diferentele de timp de descarcare.
'''

# importam librariile necesare
import os
import xarray as xr
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import geoglows 

t0 = datetime.now()

# stabilire cai pentru fisierele de date
cwd = Path.cwd()
fila_statii = os.path.join(cwd, 'config', 'coords_stations.csv')
data_folder_hist = os.path.join(cwd, 'data_init', 'historical')
data_benchmark = os.path.join(cwd, 'benchmark')

# asiguram existenta folderului de export
Path(data_folder_hist).mkdir(parents=True, exist_ok=True)
Path(data_benchmark).mkdir(parents=True, exist_ok=True)

# incarcare datele cu statiile de interes
df_stations = pd.read_csv(fila_statii)
reachs = df_stations['LINKNO'].tolist()
names = df_stations['NAME'].tolist()
benchmark_df = pd.DataFrame(columns=['tip', 'durata'])

# DESCARCAM DIRECT DIN AWS S3, FARA A FOLOSI API-UL GEOGLOWS
t1 = datetime.now()
# descarcare date istorice de la geoglows pentru statiile de interes
# pentru cele orare 
retro_hourly_zarr_uri = 's3://geoglows-v2/retrospective/hourly.zarr'
ds = xr.open_dataset(retro_hourly_zarr_uri, engine='zarr', storage_options={'anon': True})

# incarc un singur dataframe cu toate stationarile deodata
# rezultatul are index multiplu: river_id + timestamp, iar coloana Q contine debitele
# apoi se extrage cate o statie din acest dataframe si se salveaza separat
all_hist_df = ds.sel(river_id=reachs)["Q"].to_dataframe()

for reach in reachs:
    station_df = all_hist_df.xs(reach, level='river_id', drop_level=True)
    if isinstance(station_df, pd.Series):
        station_df = station_df.to_frame(name='Q')

    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Hourly.csv')
    station_df.to_csv(output_filename, index=True)
    print(f'Datele istorice orare pentru statia {locname} au fost salvate in fisierul: {output_filename}')

t2 = datetime.now()
print(f'Durata descarcarii datelor istorice orare: {t2 - t1}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_hourly_aws', 'durata': t2 - t1}

# aceeasi logica si pentru cele istorice zilnice
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
    print(f'Datele istorice zilnice pentru statia {locname} au fost salvate in fisierul: {output_filename}')

t3 = datetime.now()
print(f'Durata descarcarii datelor istorice zilnice: {t3 - t2}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_daily_aws', 'durata': t3 - t2}

# aceeasi logica si pentru cele istorice lunare
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
    print(f'Datele istorice lunare pentru statia {locname} au fost salvate in fisierul: {output_filename}')

t4 = datetime.now()
print(f'Durata descarcarii datelor istorice lunare: {t4 - t3}')
print(f'Durata totala descarcarii direct din AWS datelor istorice: {t4 - t1}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_monthly_aws', 'durata': t4 - t3}
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_total_aws', 'durata': t4 - t1}

# DESCARCAM SI DIN API-UL GEOGLOWS, PENTRU COMPARATIE
# descarcare date istorice de la geoglows pentru statiile de interes
# pentru cele orare
t5 = datetime.now() 
all_hist_df_api = geoglows.data.retrospective(river_id=reachs, format='df', resolution='hourly')
coloane = all_hist_df_api.columns.tolist()

for coloana in coloane:
    reach = int(coloana)
    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Hourly_API.csv')
    all_hist_df_api[[coloana]].to_csv(output_filename, index=True)
    print(f'Datele istorice orare pentru statia {locname} au fost salvate in fisierul: {output_filename}')

t6 = datetime.now()
print(f'Durata descarcarii datelor istorice orare din API: {t6 - t5}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_hourly_api', 'durata': t6 - t5}

# aceeasi logica si pentru cele istorice zilnice
t7 = datetime.now() 
all_hist_df_api = geoglows.data.retrospective(river_id=reachs, format='df', resolution='daily')
coloane = all_hist_df_api.columns.tolist()

for coloana in coloane:
    reach = int(coloana)
    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Daily_API.csv')
    all_hist_df_api[[coloana]].to_csv(output_filename, index=True)
    print(f'Datele istorice zilnice pentru statia {locname} au fost salvate in fisierul: {output_filename}')

t8 = datetime.now()
print(f'Durata descarcarii datelor istorice zilnice din API: {t8 - t7}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_daily_api', 'durata': t8 - t7}

# aceeasi logica si pentru cele istorice lunare
t9 = datetime.now()
all_hist_df_api = geoglows.data.retrospective(river_id=reachs, format='df', resolution='monthly')
coloane = all_hist_df_api.columns.tolist()      

for coloana in coloane:
    reach = int(coloana)
    locname = df_stations.loc[df_stations['LINKNO'] == reach, 'NAME'].values[0].replace(' ', '_')
    output_filename = os.path.join(data_folder_hist, f'{locname}_historical_Q_Monthly_API.csv')
    all_hist_df_api[[coloana]].to_csv(output_filename, index=True)
    print(f'Datele istorice lunare pentru statia {locname} au fost salvate in fisierul: {output_filename}')

t10 = datetime.now()
print(f'Durata descarcarii datelor istorice lunare din API: {t10 - t9}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_monthly_api', 'durata': t10 - t9}
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_total_api', 'durata': t10 - t5}

print(f'Durata totala descarcarii din API a datelor istorice: {t10 - t5}')
print(f'Durata totala descarcarii a datelor istorice: {t10 - t1}')
benchmark_df.loc[len(benchmark_df)] = {'tip': 'historical_total_script', 'durata': t10 - t0}

benchmark_file = os.path.join(data_benchmark, 'benchmark_historical.csv')
benchmark_df.to_csv(benchmark_file, index=False)
print('Toate datele istorice au fost descarcate cu succes!')
print('FB')