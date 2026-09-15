'''
Acest script are rolul de a descarca datele de prognoza de la geogglows pentru statiile de interes de la GRDC.
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

# stabilire cai pentru fisierele de date
cwd = Path.cwd()
fila_statii = os.path.join(cwd, 'config', 'coords_stations.csv')
data_folder_fcst = os.path.join(cwd, 'data_init', 'forecast')
data_benchmark = os.path.join(cwd, 'benchmark')

# asiguram existenta folderului de export
Path(data_folder_fcst).mkdir(parents=True, exist_ok=True)
Path(data_benchmark).mkdir(parents=True, exist_ok=True)

# incarcare datele cu statiile de interes
df_stations = pd.read_csv(fila_statii)
reachs = df_stations['LINKNO'].tolist()
names = df_stations['NAME'].tolist()

benchmark_df = pd.DataFrame(columns=['tip', 'durata'])

# GREU DE DESCARCAT DIN AWS S3, DEOARECE TREBUIE COMPUS ZILNIC LINKUL
# Asadar, pentru descarcare folosim API-ul geoglows
t1 = datetime.now()
data = t1.strftime('%Y%m%d')
# se pare ca trebuie sa revin cu o zi in urma
data = (t1 - timedelta(days=1)).strftime('%Y%m%d') # acesta linie se va comenta dupa ce se rezolva problema cu descarcarea datelor de prognoza pentru ziua curenta

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

    station_df_e = flat_ens_df[flat_ens_df.loc[:, 'river_id']==reachs[0]] 
    station_df_e = station_df_e.drop(columns=['river_id'])
    output_filename_e = os.path.join(data_folder_fcst, f'{locname}_forecast_ensembles.csv')
    station_df_e.to_csv(output_filename_e, index=False)
    print(f'Datele de prognoza stats pentru statia {locname} au fost salvate in fisierul: {output_filename_s}')
    print(f'Datele de prognoza ensembles pentru statia {locname} au fost salvate in fisierul: {output_filename_e}')

t2 = datetime.now()
print(f'Durata descarcarii datelor de prognoza: {t2 - t1}') 
benchmark_df.loc[len(benchmark_df)] = {'tip': 'forecast_all_api', 'durata': t2 - t1}


# saLvam benchmark-ul intr-un fisier csv
benchmark_file = os.path.join(data_benchmark, 'benchmark_forecast.csv')
benchmark_df.to_csv(benchmark_file, index=False)
print('Toate datele de prognoza au fost descarcate cu succes!')
print('FB')

