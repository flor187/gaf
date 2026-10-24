'''
Acest script are rolul de a analiza datele istorice de la geoglows pentru statiile de interes de la GRDC.
Testez metoda initiala de bias correction care e disponibila in geoglows. 
Mai adaug o modalitate de corectie Quantile Mapping. E provenita din libraria aceasta
https://pankajkarman.github.io/bias_correction/bias_correction.html#installation
Include o perioada de validare a prognozelor
Prognozele le va citi tot din historical geoglows si grdc
Are functie de validare personalizata a perioadei de prognoza (1985-1990) cu corectie bias pe baza perioadei de calibrare (1991-2020)
'''

# importam librariile necesare
import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import geoglows 
import plotly.graph_objects as go
from bias_correction import BiasCorrection
from geoglows.bias import _flow_and_probability_mapper

def correct_validation_period(sim_valid, sim_calib, obs_calib):
    """
    Aplică corecția MEQM antrenată pe perioada de calibrare (1991-2020)
    pe perioada de validare (1985-1990), lună cu lună.
    
    Args:
        sim_valid  : simulat GEOGloWS 1985-1990
        sim_calib  : simulat GEOGloWS 1991-2020  (antrenare CDF simulat)
        obs_calib  : observat GRDC  1991-2020    (antrenare CDF observat)
    Returns:
        DataFrame cu valorile corectate pentru 1985-1990
    """
    result = sim_valid.copy()
    
    for month in range(1, 13):
        # CDF-uri construite EXCLUSIV din perioada de calibrare
        sim_m = sim_calib[sim_calib.index.month == month].dropna()
        obs_m = obs_calib[obs_calib.index.month == month].dropna()
        
        to_prob = _flow_and_probability_mapper(sim_m, to_probability=True, extrapolate=True)
        to_flow = _flow_and_probability_mapper(obs_m, to_flow=True,        extrapolate=True)
        
        # Aplicare pe valorile din luna respectivă din 1985-1990
        mask = result.index.month == month
        vals = result.loc[mask].dropna()
        result.loc[vals.index] = to_flow(to_prob(vals.values))
    
    return result.clip(lower=0)

t0 = datetime.now()

# stabilire cai pentru fisierele de date
cwd = Path.cwd()
fila_statii = os.path.join(cwd, 'config', 'coords_stations.csv')
data_folder_hist = os.path.join(cwd, 'data_init', 'historical')
data_folder_grdc = os.path.join(cwd,'grdc_obs')
data_folder_validare = os.path.join(cwd, 'analiza', 'validare_prognoza')
data_benchmark = os.path.join(cwd, 'benchmark')
start_date = pd.Timestamp('1991-01-01')
end_date = pd.Timestamp('2020-12-31')
start_validare = pd.Timestamp('1985-01-01')
end_validare = pd.Timestamp('1990-12-31')

# asiguram existenta folderului de export
Path(data_folder_validare).mkdir(parents=True, exist_ok=True)
Path(data_benchmark).mkdir(parents=True, exist_ok=True)

# incarcare datele cu statiile de interes
df_stations = pd.read_csv(fila_statii)
names = df_stations['NAME'].tolist()

benchmark_df = pd.DataFrame(columns=['tip', 'durata'])


for name in names:
    # deschidem si pregatim pentru datele observate de la grdc
    df_grdc = pd.read_csv(os.path.join(data_folder_grdc, f'{name}_Q_Day.csv'))
    df_grdc['date'] = pd.to_datetime(df_grdc['date'])
    df_grdc = df_grdc.dropna(subset=['date']).sort_values('date').set_index('date')
    df_grdc = df_grdc.loc[start_date:end_date]

    # deschidem si pregatim pentru datele istorice de la geoglows
    df_hist = pd.read_csv(os.path.join(data_folder_hist, f'{name}_historical_Q_Daily.csv'))
    df_hist['time'] = pd.to_datetime(df_hist['time'])
    df_hist = df_hist.dropna(subset=['time']).sort_values('time').set_index('time')
    # filtram prognnoza pentru validare din perioada 1985-1990 de pe df_hist
    df_prg = df_hist.loc[start_validare:end_validare]
    df_hist = df_hist.loc[start_date:end_date]

    # pastreaza intreg intervalul din GRDC
    df_hist = df_hist.reindex(df_grdc.index)
    # daca vrei doar overlap-ul valid
    common_index = df_grdc.index.intersection(df_hist.index.dropna())
    df_grdc = df_grdc.loc[common_index]
    df_hist = df_hist.loc[common_index]

    # acum aplicam functiile de bias correction din geoglows
    #df_prg_cr = geoglows.bias.correct_forecast(forecast_data=df_prg, simulated_data=df_hist, observed_data=df_grdc, use_month=0)
    df_prg_cr = correct_validation_period(sim_valid=df_prg, sim_calib=df_hist, obs_calib=df_grdc)

    # salvare dataframe corectat 
    df_prg_cr.to_csv(os.path.join(data_folder_validare, f'{name}_forecast_prg_gw.csv'))   

    # creare grafice html si salvare
    fig_prg = geoglows.plots.retrospective(df_prg_cr, plot_type='plotly', plot_titles=[f" {name}"])
    fig_prg.write_html(os.path.join(data_folder_validare, f'{name}_forecast_prg_gw.html'), include_plotlyjs='cdn')

    print(f'Am facut pentru statia {name}')

# la quantile mapping momentan e greu de facut fiindca trebuie luate cate o coloana din prognoza in parte

t1 = datetime.now()
print(f'Durata analizei si plotarii istorice: {t1 - t0}') 
benchmark_df.loc[len(benchmark_df)] = {'tip': 'analiza_plot', 'durata': t1 - t0}
# saLvam benchmark-ul intr-un fisier csv
benchmark_file = os.path.join(data_benchmark, 'benchmark_11_validare_prognoza.csv')
benchmark_df.to_csv(benchmark_file, index=False)
print('Toate datele au fost analizate si plotate cu succes!')
print('FB')