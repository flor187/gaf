'''
Acest script are rolul de a analiza datele istorice de la geoglows pentru statiile de interes de la GRDC.
Testez metoda initiala de bias correction care e disponibila in geoglows. 
Mai adaug o modalitate de corectie Quantile Mapping. E provenita din libraria aceasta
https://pankajkarman.github.io/bias_correction/bias_correction.html#installation
'''

# importam librariile necesare
import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import geoglows 
import plotly.graph_objects as go
from bias_correction import BiasCorrection

t0 = datetime.now()

# stabilire cai pentru fisierele de date
cwd = Path.cwd()
fila_statii = os.path.join(cwd, 'config', 'coords_stations.csv')
data_folder_hist = os.path.join(cwd, 'data_init', 'historical')
data_folder_grdc = os.path.join(cwd,'grdc_obs')
data_folder_analiza = os.path.join(cwd, 'analiza', 'analiza_istorica')
data_folder_plot = os.path.join(cwd, 'data_init', 'plot_historical')
data_benchmark = os.path.join(cwd, 'benchmark')
start_date = pd.Timestamp('1991-01-01')
end_date = pd.Timestamp('2020-12-31')

# asiguram existenta folderului de export
Path(data_folder_plot).mkdir(parents=True, exist_ok=True)
Path(data_folder_analiza).mkdir(parents=True, exist_ok=True)
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
    df_hist = df_hist.loc[start_date:end_date]

    # pastreaza intreg intervalul din GRDC
    df_hist = df_hist.reindex(df_grdc.index)
    # daca vrei doar overlap-ul valid
    common_index = df_grdc.index.intersection(df_hist.index.dropna())
    df_grdc = df_grdc.loc[common_index]
    df_hist = df_hist.loc[common_index]

    # acum aplicam functiile de bias correction din geoglows
    df_hist_cr = geoglows.bias.correct_historical(simulated_data=df_hist, observed_data=df_grdc)
    tbl = geoglows.bias.statistics_tables(
        corrected= df_hist_cr,
        simulated= df_hist,
        observed= df_grdc
    )
    # salvare tabel cu metrice
    Path(data_folder_analiza, f'{name}_metrice_gw.html').write_text(tbl, encoding='utf-8')
    # salvare dataframe corectat 
    df_hist_cr.to_csv(os.path.join(data_folder_analiza, f'{name}_hist_corectat_Q_Day.csv'))

    # acum aplicam functiile de bias Quantile Mapping din libraria bias_correction
    df_hist_qm = df_hist.copy()
    bc = BiasCorrection(obs_data=df_grdc['Value'], mod_data=df_hist['Q'], sce_data=df_hist_qm['Q'])
    bqm = bc.correct(method='basic_quantile')
    bbqm = pd.DataFrame(bqm)

    tbqm = geoglows.bias.statistics_tables(
        corrected= bbqm,
        simulated= df_hist,
        observed= df_grdc
    )

    # salvare tabel cu metrice
    Path(data_folder_analiza, f'{name}_metrice_bqm.html').write_text(tbqm, encoding='utf-8')
    # salvare dataframe corectat 
    bbqm.to_csv(os.path.join(data_folder_analiza, f'{name}_hist_bqm_Q_Day.csv'))

    # plotam cu plotly
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_hist.index,
        y=df_hist['Q'],
        mode='lines',
        name='Simulate Geoglows',
        line=dict(color='rgba(240, 0, 0, 0.6)', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=df_hist_cr.index,
        y=df_hist_cr['Corrected Simulated Streamflow'],
        mode='lines',
        name='Bias Geoglows',
        line=dict(color='rgba(50, 157, 196, 0.8)', width=3)
    ))

    fig.add_trace(go.Scatter(
        x=df_hist_cr.index,
        y=bbqm['Q'],
        mode='lines',
        name='Bias Basic QM',
        line=dict(color='rgba(50, 245, 150, 0.8)', width=3)
    ))

    fig.add_trace(go.Scatter(
        x=df_grdc.index,
        y=df_grdc['Value'],
        mode='lines',
        name='Observate GRDC',
        line=dict(color='rgba(0, 0, 240, 0.6)', width=2)
    ))

    fig.update_layout(
        title='Comparatie istorica: GRDC vs GeoGlows istoric si istoric corectat',
        xaxis_title='Data',
        yaxis_title='Debitul',
        template='plotly_white',
        legend_title='Legenda',
        hovermode='x unified'
    )

    # fig.show()
    fig.write_html(os.path.join(data_folder_analiza, f'{name}_comparatie.html'), include_plotlyjs='cdn')
    print(f'Am facut pentru statia {name}')


t1 = datetime.now()
print(f'Durata analizei si plotarii istorice: {t1 - t0}') 
benchmark_df.loc[len(benchmark_df)] = {'tip': 'analiza_plot', 'durata': t1 - t0}
# saLvam benchmark-ul intr-un fisier csv
benchmark_file = os.path.join(data_benchmark, 'benchmark_05_analiza_istorica.csv')
benchmark_df.to_csv(benchmark_file, index=False)
print('Toate datele au fost analizate si plotate cu succes!')
print('FB')