'''
This script organizes data from the GRDC_OBS.txt file into a format that is easier to use for subsequent analysis.
For Romania, GRDC data is available for 19 stations, with a separate text file containing observations for each station.
As a starting point, I use code sections from the Climaax Handbook, modified and adapted to my needs.
Link workflow climaax: https://handbook.climaax.eu/notebooks/workflows/FLOODS/04_River_discharge_analysis/hazard_assessment_compare_to_observations_GRDC.html

'''

# Import required libraries
import os
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go

# Set paths for data files
cwd = Path.cwd()
data_folder_obs = os.path.join(cwd, 'grdc_obs')

# Because there are only 19 stations, the ID is set manually for each station.
grdc_nr = 6744600

# Load the initial GRDC observed-data format (.txt for each station)
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

# Create a dataframe with the observed data
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

# Export the observed-data dataframe to a CSV file
output_filename = os.path.join(data_folder_obs, f'{locname}_Q_Day.csv')
df_obs.to_csv(output_filename, index=True)

# Plot the observed data
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
# The chart opens in a web browser and can be analyzed with zoom controls or by selecting a time period.
fig.show()

# Save figure
fig.write_image(os.path.join(data_folder_obs, f'{locname}_Q_Day.png'))