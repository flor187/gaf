'''
Acest script are rolul de a plota datele de prognoza de la geoglows pentru statiile de interes de la GRDC.
Testez timpul de plotare. Initial, pe masura ce descarc plotez, iar apoi deschid csv-urile si plotez. Voi compara timpii de plotare.
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
data_folder_fcst = os.path.join(cwd, 'data_init', 'forecast')
data_folder_plot = os.path.join(cwd, 'data_init', 'plot_forecast')
data_benchmark = os.path.join(cwd, 'benchmark')

# asiguram existenta folderului de export
Path(data_folder_fcst).mkdir(parents=True, exist_ok=True)
Path(data_folder_plot).mkdir(parents=True, exist_ok=True)
Path(data_benchmark).mkdir(parents=True, exist_ok=True)

# incarcare datele cu statiile de interes
df_stations = pd.read_csv(fila_statii)
reachs = df_stations['LINKNO'].tolist()
names = df_stations['NAME'].tolist()

benchmark_df = pd.DataFrame(columns=['tip', 'durata'])

# Descarcand folosid API-ul geoglows si lundu-le pe toate odata, apoi le despartim 
t1 = datetime.now()
data = t1.strftime('%Y%m%d')
# se pare ca trebuie sa revin cu o zi in urma
# data = (t1 - timedelta(days=1)).strftime('%Y%m%d') # acesta linie se va comenta dupa ce se rezolva problema cu descarcarea datelor de prognoza pentru ziua curenta

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

    # plotare date de prognoza pentru statia curenta
    fig_s = geoglows.plots.forecast_stats(station_df_s, plot_type='plotly', plot_titles=[f" {locname}"])
    fig_s.write_html(os.path.join(data_folder_plot, f'{locname}_forecast_stats.html'), include_plotlyjs='cdn')
    # parametru include_plotlyjs='cdn' este necesar pentru a nu include libraria plotly in fisierul html, ci sa o incarce dintr-un CDN (Content Delivery Network), 
    # astfel incat fisierul html sa fie mai mic si sa se incarce mai repede
    station_df_e.set_index('time', inplace=True)
    fig_e = geoglows.plots.forecast_ensembles(station_df_e, plot_type='plotly', plot_titles=[f" {locname}"])
    fig_e.write_html(os.path.join(data_folder_plot, f'{locname}_forecast_ensembles.html'), include_plotlyjs='cdn')  

    print(f'Datele de prognoza stats pentru statia {locname} au fost salvate in fisierul: {output_filename_s}')
    print(f'Datele de prognoza ensembles pentru statia {locname} au fost salvate in fisierul: {output_filename_e}')
    print("Au fost generate si salvate ploturile de prognoza pentru statia: ", locname)

t2 = datetime.now()
print(f'Durata descarcarii toate pe API datelor de prognoza: {t2 - t1}') 
benchmark_df.loc[len(benchmark_df)] = {'tip': 'forecast_plot_all_api', 'durata': t2 - t1}

# Acum doar pentru plotare, deschidem fisierele csv si le plotam
t3 = datetime.now()

# listam fisierele csv din folderul data_init/forecast
csv_files_s = [f for f in os.listdir(data_folder_fcst) if f.endswith('stats_individual.csv')]
csv_files_e = [f for f in os.listdir(data_folder_fcst) if f.endswith('ensembles_individual.csv')]

for csv_file_s, csv_file_e in zip(csv_files_s, csv_files_e):
    locname = csv_file_s.split('_forecast_stats_individual.csv')[0]
    station_df_s = pd.read_csv(os.path.join(data_folder_fcst, csv_file_s), index_col=0)
    station_df_e = pd.read_csv(os.path.join(data_folder_fcst, csv_file_e), index_col=0)
    station_df_s.index = pd.to_datetime(station_df_s.index, utc=True)
    station_df_e.index = pd.to_datetime(station_df_e.index, utc=True) 

    # plotare date de prognoza pentru statia curenta
    fig_s = geoglows.plots.forecast_stats(station_df_s, plot_type='plotly', plot_titles=[f" {locname}"])
    fig_s.write_html(os.path.join(data_folder_plot, f'{locname}_forecast_stats_from_csv.html'), include_plotlyjs='cdn')
    fig_e = geoglows.plots.forecast_ensembles(station_df_e, plot_type='plotly', plot_titles=[f" {locname}"])
    fig_e.write_html(os.path.join(data_folder_plot, f'{locname}_forecast_ensembles_from_csv.html'), include_plotlyjs='cdn')  
    print("Au fost generate si salvate ploturile de prognoza pentru statia: ", locname) 

t4 = datetime.now()
print(f'Durata plotarii din fisierele csv a datelor de prognoza: {t4 - t3}')    
benchmark_df.loc[len(benchmark_df)] = {'tip': 'forecast_plot_from_csv', 'durata': t4 - t3}
benchmark_df.loc[len(benchmark_df)] = {'tip': f'forecast_total_plot', 'durata': t4 - t0}

# saLvam benchmark-ul intr-un fisier csv
benchmark_file = os.path.join(data_benchmark, 'benchmark_ploting.csv')
benchmark_df.to_csv(benchmark_file, index=False)
print('Toate datele de prognoza au fost descarcate cu succes!')
print('FB')

