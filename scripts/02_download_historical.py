'''
Acest script are rolul de a descarca datele istorice de la geogglows pentru statiile de interes de la GRDC.
Interogarea se face pe baza id-ului LINKNO al statiei, iar datele sunt descarcate initial in format zarr.
'''

# importam librariile necesare
import os
import xarray as xr
import pandas as pd
from pathlib import Path

# stabilire cai pentru fisierele de date
cwd = Path.cwd()
fila_statii = os.path.join(cwd, 'config', 'coords_stations.csv')
data_folder_hist = os.path.join(cwd, 'data_init', 'historical')

# asiguram existenta folderului de export
Path(data_folder_hist).mkdir(parents=True, exist_ok=True)

# incarcare datele cu statiile de interes
df_stations = pd.read_csv(fila_statii)
reachs = df_stations['LINKNO'].tolist()

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