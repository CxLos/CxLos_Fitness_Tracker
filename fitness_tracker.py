# =================================== IMPORTS ================================= #

import numpy as np 
import pandas as pd 
import plotly.express as px
import seaborn as sns 
from datetime import datetime
import os
import sys
# -------------------------------
import requests
import json
import base64
import gspread
from google.oauth2.service_account import Credentials
# --------------------------------
import dash
from dash import dcc, html, Input, Output, State, dash_table
from dash.development.base_component import Component

# 'data/~$bmhc_data_2024_cleaned.xlsx'
# print('System Version:', sys.version)

# -------------------------------------- DATA ------------------------------------------- #

current_dir = os.getcwd()
current_file = os.path.basename(__file__)
script_dir = os.path.dirname(os.path.abspath(__file__))
# print("Current Directory: \n", os.getcwd()) 

report_month = datetime(2026, 1, 1).strftime("%B")
report_year = datetime(2026, 1, 1).strftime("%Y")

# Define the Google Sheets URL
sheet_url = "https://docs.google.com/spreadsheets/d/1EXDabqzS1Gd1AteSqcovvUuJxrUMQvisf_MhnhFMeNk/edit?gid=0#gid=0"

# Define the scope
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Load credentials
encoded_key = os.getenv("GOOGLE_CREDENTIALS")

if encoded_key:
    json_key = json.loads(base64.b64decode(encoded_key).decode("utf-8"))
    creds = Credentials.from_service_account_info(json_key, scopes=scope)
else:
    creds_path = r"C:\Users\CxLos\OneDrive\Documents\Portfolio Projects\GCP\personal-projects-485203-6f6c61641541.json"
    if os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=scope)
    else:
        raise FileNotFoundError("Service account JSON file not found and GOOGLE_CREDENTIALS is not set.")

# Authorize and load the sheet
client = gspread.authorize(creds)
sheet = client.open_by_url(sheet_url)
worksheet = sheet.worksheet(f"{report_year}")
data = pd.DataFrame(worksheet.get_all_records())
raw_data = worksheet.get_all_records() 
# data = pd.DataFrame(raw_data)

# Debug: Print raw data from Google Sheets
# print("Raw data from gspread:")
# print(f"First row: {raw_data[0]}")
# print(f"Bench Press row: {[row for row in raw_data if 'Bench' in row.get('Exercise', '')][:1]}")

df = data.copy()

# -------------------------------------------------
# print(df.head())
# print(df[["Date of Activity", "Total travel time (minutes):"]])
# print('Total Marketing Events: ', len(df))
# print('Column Names: \n', df.columns.tolist())
# print('DF Shape:', df.shape)
# print('Dtypes: \n', df.dtypes)
# print('Info:', df.info())
# print("Amount of duplicate rows:", df.duplicated().sum())
# print('Current Directory:', current_dir)
# print('Script Directory:', script_dir)
# print('Path to data:',file_path)

# ================================= Columns ================================= #

columns =  [

]

# =============================== Missing Values ============================ #

# missing = df.isnull().sum()
# print('Columns with missing values before fillna: \n', missing[missing > 0])

#  Please provide public information:    137
# Please explain event-oriented:        13

# ============================== Data Preprocessing ========================== #

# Check for duplicate columns
# duplicate_columns = df.columns[df.columns.duplicated()].tolist()
# print(f"Duplicate columns found: {duplicate_columns}")
# if duplicate_columns:
#     print(f"Duplicate columns found: {duplicate_columns}")

# Get all date columns (everything except Category and Exercise)
date_columns = [col for col in df.columns if col not in ['Category', 'Exercise']]

# Debug: See what columns are being melted
# print("All columns in df:", df.columns.tolist())
# print(f"\nDate columns to melt: {date_columns}")
# print(f"\nFirst few rows of df:", df.head())

# Reshape from wide to long format
df_long = df.melt(
    id_vars=['Category', 'Exercise'],  # columns to keep
    value_vars=date_columns,  # columns to melt into rows
    var_name='Date',        # New column name
    value_name='Weight'     # New column name for cell values
)

# Convert Date to datetime
df_long['Date'] = pd.to_datetime(df_long['Date'])

# Sort by date
df_long = df_long.sort_values('Date')

# Convert Weight to numeric BEFORE creating charts
df_long['Weight'] = pd.to_numeric(df_long['Weight'], errors='coerce')

# Remove rows with NaN weights
df_long = df_long.dropna(subset=['Weight'])
df_long = df_long[df_long['Weight'].notna()]
df_long = df_long[df_long['Weight'] != '']  # Remove empty strings

print("Melted DataFrame: \n", df_long.head(10))

# =========================== Total Exercises =========================== #

total_exercises = len(df)
# print("Total events:", total_exercises)

# ========================= Push Exercises =========================== #

# Filter for Bench Press only
df_push = df_long[df_long['Category'] == 'Push']

push_line = px.line(
    df_push,
    x='Date',
    y='Weight',
    color='Exercise', 
    markers=True,
    title='Push Progress Over Time',
    labels={'Weight': 'Weight (lbs)', 'Date': 'Date'},
).update_layout(
    title=dict(
        text='Push Progress Over Time',
        x=0.5,
        xanchor='center',
        font=dict(size=20)
    ),
    xaxis=dict(
        tickformat='%m/%d'
    ),
    hovermode='closest',
    font=dict(size=12),
).update_traces(
    hovertemplate='<b>%{fullData.name}</b><br>Date: <b>%{x|%m/%d}</b><br>Weight: <b>%{y} lbs.</b><extra></extra>',
)

# ========================= Pull Exercises =========================== #

# Filter for Pull category
df_pull = df_long[df_long['Category'] == 'Pull']

pull_line = px.line(
    df_pull,
    x='Date',
    y='Weight',
    color='Exercise',
    markers=True,
    title='Pull Progress Over Time',
    labels={'Weight': 'Weight (lbs)', 'Date': 'Date'},
).update_layout(
    title=dict(
        text='Pull Progress Over Time',
        x=0.5,
        xanchor='center',
        font=dict(size=20)
    ),
    xaxis=dict(
        tickformat='%m/%d'
    ),
    hovermode='closest',
    font=dict(size=12),
).update_traces(
    hovertemplate='<b>%{fullData.name}</b><br>Date: <b>%{x|%m/%d}</b><br>Weight: <b>%{y} lbs.</b><extra></extra>',
)

# ========================= Leg Exercises =========================== #

# Filter for Leg category
df_leg = df_long[df_long['Category'] == 'Leg']

leg_line = px.line(
    df_leg,
    x='Date',
    y='Weight',
    color='Exercise',
    markers=True,
    title='Leg Progress Over Time',
    labels={'Weight': 'Weight (lbs)', 'Date': 'Date'},
).update_layout(
    title=dict(
        text='Leg Progress Over Time',
        x=0.5,
        xanchor='center',
        font=dict(size=20)
    ),
    xaxis=dict(
        tickformat='%m/%d'
    ),
    hovermode='closest',
    font=dict(size=12),
).update_traces(
    hovertemplate='<b>%{fullData.name}</b><br>Date: <b>%{x|%m/%d}</b><br>Weight: <b>%{y} lbs.</b><extra></extra>',
)

# ========================= Bicep Exercises =========================== #



# ========================= Tricep Exercises =========================== #



# ========================= Shoulder Exercises =========================== #



# ========================= Forearm Exercises =========================== #



# ========================= Ab Exercises =========================== #



# =========================  Exercises =========================== #

# =========================  Exercises =========================== #

# ========================== DataFrame Table ========================== #

# create a display index column and prepare table data/columns
# reset index to ensure contiguous numbering after any filtering/sorting upstream
df_indexed = df_long.reset_index(drop=True).copy()
# Insert '#' as the first column (1-based row numbers)
df_indexed.insert(0, '#', df_indexed.index + 1)

# Convert to records for DataTable
data = df_indexed.to_dict('records')
columns = [{"name": col, "id": col} for col in df_indexed.columns]

# ============================== Dash Application ========================== #

app = dash.Dash(__name__)
server= app.server

app.layout = html.Div(
    children=[ 
        html.Div(
            className='divv', 
            children=[ 
                html.H1(
                    f'CxLos Fitness Tracker',  
                    className='title'),
                html.Div(
                    className='btn-box', 
                    children=[
                        html.A(
                            'Repo',
                            href=f'https://github.com/CxLos/CxLos_Fitness_Tracker',
                            className='btn'
                        ),
                    ]
                ),
            ]
        ),  

# ============================ Rollups ========================== #

html.Div(
    className='rollup-row',
    children=[
        
        html.Div(
            className='rollup-box-tl',
            children=[
                html.Div(
                    className='title-box',
                    children=[
                        html.H3(
                            className='rollup-title',
                            children=[f'Total Exercises']
                        ),
                    ]
                ),

                html.Div(
                    className='circle-box',
                    children=[
                        html.Div(
                            className='circle-1',
                            children=[
                                html.H1(
                                className='rollup-number',
                                children=[total_exercises]
                            ),
                            ]
                        )
                    ],
                ),
            ]
        ),
        html.Div(
            className='rollup-box-tr',
            children=[
                html.Div(
                    className='title-box',
                    children=[
                        html.H3(
                            className='rollup-title',
                            children=['Placeholder']
                        ),
                    ]
                ),
                html.Div(
                    className='circle-box',
                    children=[
                        html.Div(
                            className='circle-2',
                            children=[
                                html.H1(
                                className='rollup-number',
                                children=['-']
                            ),
                            ]
                        )
                    ],
                ),
            ]
        ),
    ]
),

# ============================ Visuals ========================== #

html.Div(
    className='graph-container',
    children=[
        
        html.H1(
            className='visuals-text',
            children='Visuals'
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=push_line
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=pull_line
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            figure=leg_line
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            # figure=bicep_line
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            # figure=tricep_line
                        )
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            className='wide-graph',
                            # figure=shoulder_line
                        )
                    ]
                ),
            ]
        ),
    ]
),

# ============================ Data Table ========================== #

    html.Div(
        className='data-box',
        children=[
            html.H1(
                className='data-title',
                children=f'Fitness Tracker Table {report_year}'
            ),
            
            dash_table.DataTable(
                id='applications-table',
                data=data, # type: ignore
                columns=columns, # type: ignore
                page_size=10,
                sort_action='native',
                filter_action='native',
                row_selectable='multi',
                style_table={
                    'overflowX': 'auto',
                    # 'border': '3px solid #000',
                    # 'borderRadius': '0px'
                },
                style_cell={
                    'textAlign': 'left',
                    'minWidth': '100px', 
                    'whiteSpace': 'normal'
                },
                style_header={
                    'textAlign': 'center', 
                    'fontWeight': 'bold',
                    'backgroundColor': '#34A853', 
                    'color': 'white'
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_cell_conditional=[ # type: ignore
                    # make the index column narrow and centered
                    {'if': {'column_id': '#'},
                    'style': {'width': '20px', 'minWidth': '60px', 'maxWidth': '60px', 'textAlign': 'center'}},

                    {'if': {'column_id': 'Description'},
                    'style': {'width': '350px', 'minWidth': '200px', 'maxWidth': '400px'}},

                    {'if': {'column_id': 'Tags'},
                    'style': {'width': '250px', 'minWidth': '200px', 'maxWidth': '400px'}},

                    {'if': {'column_id': 'Collab'},
                    'style': {'width': '250px', 'minWidth': '200px', 'maxWidth': '400px'}},
                ]
            ),
        ]
    ),
])

print(f"Serving Flask app '{current_file}'! 🚀")

if __name__ == '__main__':
    app.run(debug=
                   True)
                #    False)

# -------------------------------------------- KILL PORT ---------------------------------------------------

# netstat -ano | findstr :8050
# taskkill /PID 24772 /F
# npx kill-port 8050

# ---------------------------------------------- Host Application -------------------------------------------

# 1. pip freeze > requirements.txt
# 2. add this to procfile: 'web: gunicorn impact_11_2024:server'
# 3. heroku login
# 4. heroku create
# 5. git push heroku main

# Create venv 
# virtualenv venv 
# source venv/bin/activate # uses the virtualenv

# Update PIP Setup Tools:
# pip install --upgrade pip setuptools

# Install all dependencies in the requirements file:
# pip install -r requirements.txt

# Check dependency tree:
# pipdeptree
# pip show package-name

# Remove
# pypiwin32
# pywin32
# jupytercore

# ----------------------------------------------------

# Name must start with a letter, end with a letter or digit and can only contain lowercase letters, digits, and dashes.

# Heroku Setup:
# heroku login
# heroku create admin-jun-25
# heroku git:remote -a admin-jun-25
# git push heroku main

# Clear Heroku Cache:
# heroku plugins:install heroku-repo
# heroku repo:purge_cache -a mc-impact-11-2024

# Set buildpack for heroku
# heroku buildpacks:set heroku/python

# Heatmap Colorscale colors -----------------------------------------------------------------------------

#   ['aggrnyl', 'agsunset', 'algae', 'amp', 'armyrose', 'balance',
            #  'blackbody', 'bluered', 'blues', 'blugrn', 'bluyl', 'brbg',
            #  'brwnyl', 'bugn', 'bupu', 'burg', 'burgyl', 'cividis', 'curl',
            #  'darkmint', 'deep', 'delta', 'dense', 'earth', 'edge', 'electric',
            #  'emrld', 'fall', 'geyser', 'gnbu', 'gray', 'greens', 'greys',
            #  'haline', 'hot', 'hsv', 'ice', 'icefire', 'inferno', 'jet',
            #  'magenta', 'magma', 'matter', 'mint', 'mrybm', 'mygbm', 'oranges',
            #  'orrd', 'oryel', 'oxy', 'peach', 'phase', 'picnic', 'pinkyl',
            #  'piyg', 'plasma', 'plotly3', 'portland', 'prgn', 'pubu', 'pubugn',
            #  'puor', 'purd', 'purp', 'purples', 'purpor', 'rainbow', 'rdbu',
            #  'rdgy', 'rdpu', 'rdylbu', 'rdylgn', 'redor', 'reds', 'solar',
            #  'spectral', 'speed', 'sunset', 'sunsetdark', 'teal', 'tealgrn',
            #  'tealrose', 'tempo', 'temps', 'thermal', 'tropic', 'turbid',
            #  'turbo', 'twilight', 'viridis', 'ylgn', 'ylgnbu', 'ylorbr',
            #  'ylorrd'].

# rm -rf ~$bmhc_data_2024_cleaned.xlsx
# rm -rf ~$bmhc_data_2024.xlsx
# rm -rf ~$bmhc_q4_2024_cleaned2.xlsx