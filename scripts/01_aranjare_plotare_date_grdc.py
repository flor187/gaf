'''
Acest script are scopul de a aranja datele din fișierul GRDC_OBS.txt într-un format mai ușor de utilizat pentru analiza ulterioară.
Pentru Romania sunt disponibile date GRDC pentru 19 stații, iar pentru fiecare stație există un fișier text separat cu datele observate.
Ca baza de pornire folosesc bucati de cod din Climaax Handbook, dar am modificat și adaptat pentru a se potrivi nevoilor mele.
Link workflow climaax: https://handbook.climaax.eu/notebooks/workflows/FLOODS/04_River_discharge_analysis/hazard_assessment_compare_to_observations_GRDC.html

'''

# importarea librariilor necesare
import os
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go

# stabilire cai pentru fisierele de date
cwd = Path.cwd()
data_folder_obs = os.path.join(cwd, 'grdc_obs')

# Fiindca sunt doar 19 statii id-ul se pune manual pentru fiecare statie in parte. 
grdc_nr = 6744600

# incarcare date observate grdc format initial (.txt pentru fiecare statie)
filename = os.path.join(data_folder_obs, f'{grdc_nr}_Q_Day.Cmd.txt')
metadata = {}
with open(filename, 'r', encoding='cp1252') as f:
    for line in f:
        if line.startswith('#'):  # only look at metadata lines
            clean = line[1:].strip() # Remove "#" and strip spaces
            if ":" in clean:  # only lines with "key: value"
                key, value = clean.split(':', 1)
                metadata[key.strip()] = value.strip()
        else:
            break  # stop when actual data starts

locname = metadata.get('Station').replace(' ', '_')
lat = float(metadata.get('Latitude (DD)', 'nan'))
lon = float(metadata.get('Longitude (DD)', 'nan'))
loc = [lon, lat]
print(f'Station {locname}: {loc}')

# creare dataframe cu datele observate
df_obs = pd.read_csv(
    filename,
    comment='#',
    sep=';',
    skipinitialspace=True, 
    na_values=['--:--', -999.000],
    encoding='cp1252'
)

df_obs = df_obs.drop(columns='hh:mm').rename(columns={'YYYY-MM-DD': 'date'})
df_obs['date'] = pd.to_datetime(df_obs['date'], format='%Y-%m-%d')
df_obs.set_index('date', inplace=True)

# exportare dataframe cu datele observate intr-un fisier csv
output_filename = os.path.join(data_folder_obs, f'{locname}_Q_Day.csv')
df_obs.to_csv(output_filename, index=True)

#plotarea datelor observate
# Create a figure
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_obs.index, y=df_obs['Value'], mode='lines', name='observations'
))

# Customize layout
fig.update_layout(
    height=500, width=1100,
    title_text=(
        '<b>Daily timeseries of river discharges from GRDC database</b><br>'
        f'station nr. {grdc_nr}, {locname}'
    ),
    yaxis_title='River discharge [m3/s]',
    showlegend=False,
)

# Show the figure
# Graficul se deschide intr-un browser web si poate fi analizat prin zoom in si zoom out, dar si prin selectarea unei anumite perioade de timp.
fig.show()

# Save figure
fig.write_image(os.path.join(data_folder_obs, f'{locname}_Q_Day.png'))