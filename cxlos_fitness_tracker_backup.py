
# =================================== IMPORTS ================================= #

import pandas as pd 
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
# import sys
# -------------------------------
# import requests
import json
import base64
import gspread
from google.oauth2.service_account import Credentials
# --------------------------------
from dash import dash, dcc, html, Input, Output, dash_table
# from dash.development.base_component import Component

# 'data/~$bmhc_data_2024_cleaned.xlsx'
# print('System Version:', sys.version)

# -------------------------------------- DATA ------------------------------------------- #

current_dir = os.getcwd()
current_file = os.path.basename(__file__)
script_dir = os.path.dirname(os.path.abspath(__file__))
# print("Current Directory: \n", os.getcwd()) 

report_month = datetime(2026, 1, 1).strftime("%B")
report_year = datetime(2026, 1, 1).strftime("%Y")
name = "CxLos"

# Define the Google Sheets URL
# sheet_url = 
sheet_url = "https://docs.google.com/spreadsheets/d/1X5ZQo9OmAwQFsiBaxRoH8-L3kGrjDt20Em7W3NYb2qI/edit?resourcekey=&gid=1791797530#gid=1791797530"

# Define the scope
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Load credentials
encoded_key = os.getenv("GOOGLE_CREDENTIALS")

if encoded_key:
    # Render: GOOGLE_CREDENTIALS is BASE64 ENCODED JSON
    json_key = json.loads(
        base64.b64decode(encoded_key).decode("utf-8")
    )
    creds = Credentials.from_service_account_info(json_key, scopes=scope)

else:
    # Local development fallback
    creds_path = r"C:\Users\CxLos\OneDrive\Documents\Portfolio Projects\GCP\personal-projects-485203-6f6c61641541.json"

    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            "Service account JSON file not found and GOOGLE_CREDENTIALS is not set."
        )

    creds = Credentials.from_service_account_file(creds_path, scopes=scope)

# Authorize and load the sheet
client = gspread.authorize(creds)
sheet = client.open_by_url(sheet_url)

# ============================== Data Loading Function ========================== #


def load_data_for_year(year):
    """Load and process fitness data for a specific year from a single-sheet spreadsheet"""
    try:
        # Load all data from the first sheet
        data = pd.DataFrame(client.open_by_url(sheet_url).sheet1.get_all_records())
        df_loaded = data.copy()
        # Trim leading and trailing whitespaces from column names
        df_loaded.columns = df_loaded.columns.str.strip()
        # Convert 'Date of Activity' to datetime
        df_loaded["Date"] = pd.to_datetime(df_loaded["Date"], errors='coerce')
        # If year is 'All Time', return all data
        if year == 'All Time':
            filtered_df = df_loaded.copy()
        else:
            # Filter by year (as int)
            try:
                year_int = int(year)
            except Exception:
                year_int = pd.Timestamp.now().year
            filtered_df = df_loaded[df_loaded['Date'].dt.year == year_int]
        # Sort by date
        filtered_df = filtered_df.sort_values(by='Date', ascending=True)
        # Strip whitespace from string entries in the whole DataFrame
        for col in filtered_df.select_dtypes(include='object').columns:
            filtered_df[col] = filtered_df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
        return filtered_df.copy()
    except Exception as e:
        print(f"❌ ERROR loading data for {year}: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

# Load default year (All Time)
df = load_data_for_year('All Time')

# -------------------------------------------------
# print(df.head())
# print('Total Workouts: ', len(df))
# print('Column Names: \n', df.columns.tolist())
# print('DF Shape:', df.shape)
# print('Dtypes: \n', df.dtypes)
# print('Info:', df.info())
# print('Current Directory:', current_dir)
# print('Script Directory:', script_dir)
# print('Path to data:',file_path)

# ================================= Columns ================================= #

columns =  [
'Timestamp', 'Date', 'Push Exercise', 'Triceps Exercise', 'Pull Exercise', 'Leg Exercise', 'Bicep Exercise', 'Shoulder Exercise', 'Forearm Exercise', 'Abs Exercise', 'Calisthenics Exercise', 'Cardio Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5', 'Time', 'Distance', 'Floors', 'Calories'
]

# =============================== Missing Values ============================ #

# missing = df.isnull().sum()
# print('Columns with missing values before fillna: \n', missing[missing > 0])

#  Please provide public information:    137
# Please explain event-oriented:        13

# ============================== Data Preprocessing ========================== #

# print("Melted DataFrame: \n", df_long.head(10))

# ============================== Line Chart ========================== #

# Helper to build line charts without relying on Plotly Express grouping
def make_line_chart(df_cat: pd.DataFrame, title: str, exercise_col: str) -> go.Figure:
    fig = go.Figure()

    if df_cat.empty:
        fig.update_layout(title=dict(text=title, x=0.5, xanchor='center', font=dict(size=20)))
        return fig

    # Cardio logic: use correct metric for each exercise
    if exercise_col == 'Cardio Exercise':
        cardio_metric_map = {
            'Bike': ('Distance', 'Miles'),
            'Indoor Run': ('Distance', 'Miles'),
            'Outdoor Run': ('Distance', 'Miles'),
            'Stair Master': ('Floors', 'Floors')
        }
        for exercise_name, sub in df_cat.groupby(exercise_col):
            metric_col, unit = cardio_metric_map.get(exercise_name, ('Distance', 'Value'))
            sub_sorted = sub.sort_values('Date')
            if metric_col in sub_sorted:
                fig.add_trace(
                    go.Scatter(
                        x=sub_sorted['Date'],
                        y=sub_sorted[metric_col],
                        mode='lines+markers',
                        name=f'{exercise_name} ({unit})',
                        hovertemplate=f'Exercise: <b>%{{fullData.name}}</b><br>Date: <b>%{{x|%m/%d/%Y}}</b><br>{unit}: <b>%{{y}}</b><extra></extra>',
                    )
                )
        yaxis_title = 'Miles / Floors'
    else:
        for exercise_name, sub in df_cat.groupby(exercise_col):
            sub_sorted = sub.sort_values('Date')
            # Build hovertemplate with Set 1-5 if present
            set_cols = [col for col in ['Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5'] if col in sub_sorted.columns]
            set_template = ''.join([f'<br>{col}: <b>%{{customdata[{i}]}}</b>' for i, col in enumerate(set_cols)])
            hovertemplate = (
                f'Exercise: <b>%{{fullData.name}}</b>'
                f'<br>Date: <b>%{{x|%m/%d/%Y}}</b>'
                f'<br>Weight: <b>%{{y}} lbs.</b>'
                f'{set_template}'
                '<extra></extra>'
            )
            customdata = sub_sorted[set_cols].values if set_cols else None
            fig.add_trace(
                go.Scatter(
                    x=sub_sorted['Date'],
                    y=sub_sorted['Weight'],
                    mode='lines+markers',
                    name=str(exercise_name),
                    hovertemplate=hovertemplate,
                    customdata=customdata
                )
            )
        yaxis_title = 'Weight (lbs)'

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=20)),
        xaxis=dict(tickformat='%m/%d/%Y', title='Date'),
        yaxis=dict(title=yaxis_title),
        hovermode='closest',
        font=dict(size=12),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    return fig

# =========================== Initial Empty Figures =========================== #

# Create empty figures for initial load
empty_fig = go.Figure()
empty_fig.update_layout(title=dict(text='Please Select a Year', x=0.5, font=dict(size=20)))

# ========================== DataFrame Table ========================== #

# create a display index column and prepare table data/columns
df_indexed = df.reset_index(drop=True).copy()

# Reorder columns: Date first, then the rest
# column_order = ['Date', 'Category', 'Exercise', 'Weight']
# df_indexed = df_indexed[column_order]

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
                    f"{name} Fitness Tracker",  
                    className='title'),
                dcc.Loading(
                    id='year-subtitle-loading',
                    type='circle',
                    color='red',
                    style={'display': 'inline-flex', 'alignItems': 'center', 'gap': '10px'},
                    children=html.H1(
                        id='year-subtitle',
                        children='All Time',
                        className='title2',
                        style={'margin': '0'}
                    )
                ),
                html.Div(
                    className='dropdown-container',
                    children=[
                        html.Label('', style={'marginRight': '10px', 'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='year-dropdown',
                            options=[
                                {'label': 'All Time', 'value': 'All Time'},
                                {'label': '2026', 'value': '2026'},
                            ],
                            # value='All Time',
                            value=None,
                            placeholder='Select Year',  # Add this line
                            clearable=False,
                            style={
                                'width': '150px',
                                'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Calibri, Arial, sans-serif',
                                'backgroundColor': 'rgb(253, 180, 180)',
                                'border': '2px solid rgb(217, 24, 24)',
                                'borderRadius': '50px'
                            }
                        ),
                    ],
                    style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'margin': '20px 0'}
                ),
                html.Div(
                    className='btn-box', 
                    children=[
                        html.A(
                            'Repo',
                            href=f'https://github.com/CxLos/{name}_Fitness_Tracker',
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
                            id='total-exercises-title',
                            className='rollup-title',
                            children=[f'Total Gym Days']
                        ),
                    ]
                ),

                html.Div(
                    className='circle-box-1',
                    children=[
                        html.Div(
                            className='circle-1',
                            children=[
                                html.H1(
                                    id='total-exercises',
                                className='rollup-number',
                                children=['-']
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
                            id='-days-title',
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
                                id='-days',
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
        
        # html.H1(
        #     className='visuals-text',
        #     children='Visuals'
        # ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='push-days-title',
                                    className='rollup-title',
                                    children=['Total Push Days']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='push-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='push-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='push-bar',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='push-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='pull-days-title',
                                    className='rollup-title',
                                    children=[f'Total Pull Days']
                                ),
                            ]
                        ),

                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                            id='pull-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='pull-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='pull-bar',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='pull-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='leg-days-title',
                                    className='rollup-title',
                                    children=['Total Leg Days']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='leg-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='leg-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='leg-bar',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='leg-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='bicep-days-title',
                                    className='rollup-title',
                                    children=['Total Bicep Days']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='bicep-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='bicep-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='bicep-bar',
                                    className='graph',
                                    figure=empty_fig    
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='bicep-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='tricep-days-title',
                                    className='rollup-title',
                                    children=['Total Tricep Days']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='tricep-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='tricep-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='tricep-bar',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='tricep-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='shoulder-days-title',
                                    className='rollup-title',
                                    children=['Total Shoulder Days']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='shoulder-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='shoulder-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='shoulder-bar',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='shoulder-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),

        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='calisthenics-days-title',
                                    className='rollup-title',
                                    children=['Total Calisthenics Days']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='calisthenics-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='calisthenics-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='calisthenics-bar',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='calisthenics-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),

                
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='ab-days-title',
                                    className='rollup-title',
                                    children=['Total  Days']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='ab-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='ab-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='ab-bar',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='ab-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='forearm-days-title',
                                    className='rollup-title',
                                    children=['Total Forearm Days']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='forearm-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='forearm-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='forearm-bar',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='forearm-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                    ]
                ),
            ]
        ),
        
        html.Div(
            className='graph-row',
            children=[
                html.Div(
                    className='rollup-box',
                    children=[
                        html.Div(
                            className='title-box',
                            children=[
                                html.H3(
                                    id='cardio-days-title',
                                    className='rollup-title',
                                    children=['Total Cardio Days']
                                ),
                            ]
                        ),
                        html.Div(
                            className='circle-box',
                            children=[
                                html.Div(
                                    className='circle',
                                    children=[
                                        html.H1(
                                        id='cardio-days',
                                        className='rollup-number',
                                        children=['-']
                                    ),
                                    ]
                                )
                            ],
                        ),
                    ]
                ),
                html.Div(
                    className='wide-box',
                    children=[
                        dcc.Graph(
                            id='cardio-graph',
                            className='wide-graph',
                            figure=empty_fig
                        )
                    ]
                ),
                html.Div(
                    className='graph-row-1',
                    children=[
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='cardio-bar',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
                        html.Div(
                            className='graph-box',
                            children=[
                                dcc.Graph(
                                    id='cardio-pie',
                                    className='graph',
                                    figure=empty_fig
                                )
                            ]
                        ),
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
                id='table-title',
                className='data-title',
                children=f'Fitness Tracker Table {report_year}'
            ),
            
            dash_table.DataTable(
                id='applications-table',
                data=[], # type: ignore
                columns=[], # type: ignore
                page_size=20,
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
                    'backgroundColor': "#FF0000", 
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

# ============================== Callback ========================== #

@app.callback(
    [
        Output('year-subtitle', 'children'),
        Output('total-exercises-title', 'children'),
        Output('total-exercises', 'children'),
        Output('push-days-title', 'children'),
        Output('push-days', 'children'),
        Output('pull-days-title', 'children'),
        Output('pull-days', 'children'),
        Output('leg-days-title', 'children'),
        Output('leg-days', 'children'),
        Output('bicep-days-title', 'children'),
        Output('bicep-days', 'children'),
        Output('tricep-days-title', 'children'),
        Output('tricep-days', 'children'),
        Output('shoulder-days-title', 'children'),
        Output('shoulder-days', 'children'),
        Output('calisthenics-days-title', 'children'),
        Output('calisthenics-days', 'children'),
        Output('ab-days-title', 'children'),
        Output('ab-days', 'children'),
        Output('forearm-days-title', 'children'),
        Output('forearm-days', 'children'),
        Output('cardio-days-title', 'children'),
        Output('cardio-days', 'children'),
        Output('push-graph', 'figure'),
        Output('push-bar', 'figure'),
        Output('push-pie', 'figure'),
        Output('pull-graph', 'figure'),
        Output('pull-bar', 'figure'),
        Output('pull-pie', 'figure'),
        Output('leg-graph', 'figure'),
        Output('leg-bar', 'figure'),
        Output('leg-pie', 'figure'),
        Output('bicep-graph', 'figure'),
        Output('bicep-bar', 'figure'),
        Output('bicep-pie', 'figure'),
        Output('tricep-graph', 'figure'),
        Output('tricep-bar', 'figure'),
        Output('tricep-pie', 'figure'),
        Output('shoulder-graph', 'figure'),
        Output('shoulder-bar', 'figure'),
        Output('shoulder-pie', 'figure'),
        Output('ab-graph', 'figure'),
        Output('ab-bar', 'figure'),
        Output('ab-pie', 'figure'),
        Output('calisthenics-graph', 'figure'),
        Output('calisthenics-bar', 'figure'),
        Output('calisthenics-pie', 'figure'),
        Output('forearm-graph', 'figure'),
        Output('forearm-bar', 'figure'),
        Output('forearm-pie', 'figure'),
        Output('cardio-graph', 'figure'),
        Output('cardio-bar', 'figure'),
        Output('cardio-pie', 'figure'),
        Output('table-title', 'children'),
        Output('applications-table', 'data'),
        Output('applications-table', 'columns'),
    ],
    [Input('year-dropdown', 'value')],
    # prevent_initial_call=True
    # prevent_initial_call=False 
)
def update_dashboard(selected_year):

    # If no year is selected, show empty dashboard
    if selected_year is None:
        return (
            '',  # year_subtitle
            '',  # rollup_title
            '-',  # total
            *[''] * 20,  # All other text outputs
            *[empty_fig] * 30,  # All graph outputs
            '',  # table_title
            [],  # table_data
            []   # table_columns
        )

    try:
        print(f"🔄 Callback triggered for year: {selected_year}")
        
        # Load data for selected year
        df_year = load_data_for_year(selected_year)
        # print(f"✅ Loaded {len(df_year)} rows for {selected_year}")
        
        # ...existing code...
        
    except Exception as e:
        print(f"❌ ERROR in callback: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return empty/error state
        return (
            f"Error: {selected_year}",
            "Error loading data",
            0,
            *["Error"] * 20,  # All other text outputs
            *[empty_fig] * 30,  # All graph outputs
            "Error loading table",
            [],
            []
        )

    # Load data for selected year
    df_year = load_data_for_year(selected_year)
    
# Filter and select columns for each muscle group
    df_push = df_year[['Date', 'Push Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']].dropna(subset=['Push Exercise'])
    df_triceps = df_year[['Date', 'Triceps Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']].dropna(subset=['Triceps Exercise'])
    df_pull = df_year[['Date', 'Pull Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']].dropna(subset=['Pull Exercise'])
    df_leg = df_year[['Date', 'Leg Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']].dropna(subset=['Leg Exercise'])
    df_bicep = df_year[['Date', 'Bicep Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']].dropna(subset=['Bicep Exercise'])
    df_shoulder = df_year[['Date', 'Shoulder Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']].dropna(subset=['Shoulder Exercise'])
    df_forearm = df_year[['Date', 'Forearm Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']].dropna(subset=['Forearm Exercise'])
    df_abs = df_year[['Date', 'Abs Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']].dropna(subset=['Abs Exercise'])
    df_calisthenics = df_year[['Date', 'Calisthenics Exercise', 'Weight', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']].dropna(subset=['Calisthenics Exercise'])
    df_cardio = df_year[['Date', 'Cardio Exercise', 'Time', 'Distance', 'Floors', 'Calories']].dropna(subset=['Cardio Exercise'])

    df_push = df_push[df_push['Push Exercise'].str.strip() != '']
    df_pull = df_pull[df_pull['Pull Exercise'].str.strip() != '']
    df_leg = df_leg[df_leg['Leg Exercise'].str.strip() != '']
    df_bicep = df_bicep[df_bicep['Bicep Exercise'].str.strip() != '']
    df_triceps = df_triceps[df_triceps['Triceps Exercise'].str.strip() != '']
    df_shoulder = df_shoulder[df_shoulder['Shoulder Exercise'].str.strip() != '']
    df_abs = df_abs[df_abs['Abs Exercise'].str.strip() != '']
    df_forearm = df_forearm[df_forearm['Forearm Exercise'].str.strip() != '']
    df_calisthenics = df_calisthenics[df_calisthenics['Calisthenics Exercise'].str.strip() != '']
    df_cardio = df_cardio[df_cardio['Cardio Exercise'].str.strip() != '']

    # Calculate total unique gym days (unique dates)
    total = df_year['Date'].nunique()
    
    # Create graphs for each category

    push_days = df_push['Date'].nunique() if not df_push.empty else 0
    push_fig = make_line_chart(df_push, f'Push Progress Over Time - {selected_year}',"Push Exercise")
    print("Push DF: \n", df_push)

    df_push_counts = df_push['Push Exercise'].value_counts().reset_index()
    df_push_counts.columns = ['Push Exercise', 'Count']

    push_bar_fig = px.bar(
        df_push_counts,
        y="Push Exercise",
        x='Count',
        color="Push Exercise",
        text='Count',
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Push Exercise Bar Chart - {selected_year}',
            x=0.5,
            font=dict(size=21,
            family='Calibri',
            color='black')
        ),
        font=dict(
            family='Calibri',
            size=16,
            color='black'
        ),
        yaxis=dict(
            tickfont=dict(size=16),
            title=dict(
                text="Push Exercise",
                font=dict(size=16)
            )
        ),
        xaxis=dict(
            title=dict(
                text='Count',
                font=dict(size=16)
            )
        ),
        legend=dict(visible=False),
        hovermode='closest',
        bargap=0.08,
        bargroupgap=0
    ).update_traces(
        textposition='auto',
        hovertemplate='<b>Push Exercise:</b> %{y}<br><b>Count</b>: %{x}<extra></extra>'
    )

    push_pie_fig = px.pie(
        df_push_counts,
        names="Push Exercise",
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Push Exercise Distribution - {selected_year}',
            x=0.5,
            font=dict(
                size=21,
                family='Calibri',
                color='black'
            )
        ),
        font=dict(
            family='Calibri',
            size=16,
            color='black'
        )
    ).update_traces(
        rotation=100,
        texttemplate='%{percent:.1%}',
        hovertemplate='<b>Push Exercise:</b> %{label}<br><b>Count</b>: %{value}<extra></extra>'
    )
    
    pull_days = df_pull['Date'].nunique() if not df_pull.empty else 0
    pull_fig = make_line_chart(df_pull, f'Pull Progress Over Time - {selected_year}',"Pull Exercise")

    df_pull_counts = df_pull['Pull Exercise'].value_counts().reset_index()
    df_pull_counts.columns = ['Pull Exercise', 'Count']

    pull_bar_fig = px.bar(
        df_pull_counts, 
        y="Pull Exercise", 
        x='Count', 
        color="Pull Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Pull Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Pull Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Pull Exercise:</b> %{y}<br><b>Count</b>: %{x}<extra></extra>'
    )

    pull_pie_fig = px.pie(
        df_pull_counts, 
        names="Pull Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Pull Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>Pull Exercise:</b> %{label}<br><b>Count</b>: %{value}<extra></extra>'
    )
    
    leg_days = df_leg['Date'].nunique() if not df_leg.empty else 0
    leg_fig = make_line_chart(df_leg, f'Leg Progress Over Time - {selected_year}', "Leg Exercise")

    df_leg_counts = df_leg['Leg Exercise'].value_counts().reset_index()
    df_leg_counts.columns = ['Leg Exercise', 'Count']

    leg_bar_fig = px.bar(
        df_leg_counts, 
        y="Leg Exercise", 
        x='Count', 
        color="Leg Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Leg Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Leg Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Leg Exercise:</b> %{y}<br><b>Count</b>: %{x}<extra></extra>'
    )

    leg_pie_fig = px.pie(
        df_leg_counts, 
        names="Leg Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Leg Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>Leg Exercise:</b> %{label}<br><b>Count</b>: %{value}<extra></extra>'
    )
    
    # Calculate bicep days
    bicep_days = df_bicep['Date'].nunique() if not df_bicep.empty else 0
    bicep_fig = make_line_chart(df_bicep, f'Bicep Progress Over Time - {selected_year}', "Bicep Exercise")

    df_bicep_counts = df_bicep['Bicep Exercise'].value_counts().reset_index()
    df_bicep_counts.columns = ['Bicep Exercise', 'Count']
    
    bicep_bar_fig = px.bar(
        df_bicep_counts, 
        y="Bicep Exercise", 
        x='Count', 
        color="Bicep Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Bicep Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    bicep_pie_fig = px.pie(
        df_bicep_counts, 
        names="Bicep Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Bicep Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    tricep_days = df_triceps['Date'].nunique() if not df_triceps.empty else 0
    tricep_fig = make_line_chart(df_triceps, f'Triceps Progress Over Time - {selected_year}', "Triceps Exercise")

    df_tricep_counts = df_triceps['Triceps Exercise'].value_counts().reset_index()
    df_tricep_counts.columns = ['Triceps Exercise', 'Count']

    tricep_bar_fig = px.bar(
        df_tricep_counts, 
        y="Triceps Exercise", 
        x='Count', 
        color="Triceps Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Triceps Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    tricep_pie_fig = px.pie(
        df_tricep_counts, 
        names="Triceps Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Triceps Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    shoulder_days = df_shoulder['Date'].nunique() if not df_shoulder.empty else 0
    shoulder_fig = make_line_chart(df_shoulder, f'Shoulder Progress Over Time - {selected_year}', "Shoulder Exercise")

    df_shoulder_counts = df_shoulder['Shoulder Exercise'].value_counts().reset_index()
    df_shoulder_counts.columns = ['Shoulder Exercise', 'Count']

    shoulder_bar_fig = px.bar(
        df_shoulder_counts, 
        y="Shoulder Exercise", 
        x='Count', 
        color="Shoulder Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Shoulder Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    shoulder_pie_fig = px.pie(
        df_shoulder_counts, 
        names="Shoulder Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Shoulder Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    ab_days = df_abs['Date'].nunique() if not df_abs.empty else 0
    ab_fig = make_line_chart(df_abs, f'Abs Progress Over Time - {selected_year}', "Abs Exercise")

    df_ab_counts = df_abs['Abs Exercise'].value_counts().reset_index()
    df_ab_counts.columns = ['Abs Exercise', 'Count']

    ab_bar_fig = px.bar(
        df_ab_counts, 
        y="Abs Exercise", 
        x='Count', 
        color="Abs Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Abs Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    ab_pie_fig = px.pie(
        df_ab_counts, 
        names="Abs Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Abs Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    calisthenics_days = df_calisthenics['Date'].nunique() if not df_calisthenics.empty else 0
    calisthenics_fig = make_line_chart(df_calisthenics, f'Calisthenics Progress Over Time - {selected_year}', "Calisthenics Exercise")

    df_calisthenics_counts = df_calisthenics['Calisthenics Exercise'].value_counts().reset_index()
    df_calisthenics_counts.columns = ['Calisthenics Exercise', 'Count']

    calisthenics_bar_fig = px.bar(
        df_calisthenics_counts, 
        y="Calisthenics Exercise", 
        x='Count', 
        color="Calisthenics Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Calisthenics Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    calisthenics_pie_fig = px.pie(
        df_calisthenics_counts, 
        names="Calisthenics Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Calisthenics Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    forearm_days = df_forearm['Date'].nunique() if not df_forearm.empty else 0
    forearm_fig = make_line_chart(df_forearm, f'Forearm Progress Over Time - {selected_year}', "Forearm Exercise")

    df_forearm_counts = df_forearm['Forearm Exercise'].value_counts().reset_index()
    df_forearm_counts.columns = ['Forearm Exercise', 'Count']

    forearm_bar_fig = px.bar(
        df_forearm_counts,
        y="Forearm Exercise",
        x='Count',
        color="Forearm Exercise",
        text='Count',
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Forearm Exercise Bar Chart - {selected_year}',
            x=0.5,
            font=dict(
                size=21,
                family='Calibri',
                color='black'
            )
        ),
        font=dict(
            family='Calibri',
            size=16,
            color='black'
        ),
        yaxis=dict(
            tickfont=dict(size=16),
            title=dict(
                text="Forearm Exercise",
                font=dict(size=16)
            )
        ),
        xaxis=dict(
            title=dict(
                text='Count',
                font=dict(size=16)
            )
        ),
        legend=dict(visible=False),
        hovermode='closest',
        bargap=0.08,
        bargroupgap=0
    ).update_traces(
        textposition='auto',
        hovertemplate='<b>Forearm Exercise:</b> %{y}<br><b>Count</b>: %{x}<extra></extra>'
    )

    forearm_pie_fig = px.pie(
        df_forearm_counts,
        names="Forearm Exercise",
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Forearm Exercise Distribution - {selected_year}',
            x=0.5,
            font=dict(
                size=21,
                family='Calibri',
                color='black'
            )
        ),
        font=dict(
            family='Calibri',
            size=16,
            color='black'
        )
    ).update_traces(
        rotation=100,
        texttemplate='%{percent:.1%}',
        hovertemplate='<b>Forearm Exercise:</b> %{label}<br><b>Count</b>: %{value}<extra></extra>'
    )

    df_bicep_counts = df_bicep['Bicep Exercise'].value_counts().reset_index()
    df_bicep_counts.columns = ['Bicep Exercise', 'Count']

    bicep_bar_fig = px.bar(
        df_bicep_counts, 
        y="Bicep Exercise", 
        x='Count', 
        color="Bicep Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Bicep Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Bicep Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Bicep Exercise:</b> %{y}<br><b>Count</b>: %{x}<extra></extra>'
    )

    bicep_pie_fig = px.pie(
        df_bicep_counts, 
        names="Bicep Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Bicep Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>Bicep Exercise:</b> %{label}<br><b>Count</b>: %{value}<extra></extra>'
    )
    
    cardio_days = df_cardio['Date'].nunique() if not df_cardio.empty else 0
    # Cardio line chart: plot each exercise with its correct metric
    import plotly.graph_objects as go
    cardio_metric_map = {
        'Bike': ('Distance', 'Miles'),
        'Indoor Run': ('Distance', 'Miles'),
        'Outdoor Run': ('Distance', 'Miles'),
        'Stair Master': ('Floors', 'Floors')
    }
    cardio_fig = make_line_chart(df_cardio, f'Cardio Progress Over Time - {selected_year}', 'Cardio Exercise')

    df_cardio_counts = df_cardio['Cardio Exercise'].value_counts().reset_index()
    df_cardio_counts.columns = ['Cardio Exercise', 'Count']

    cardio_bar_fig = px.bar(
        df_cardio_counts, 
        y="Cardio Exercise", 
        x='Count', 
        color="Cardio Exercise", 
        text='Count', 
        orientation='h'
    ).update_layout(
        title=dict(
            text=f'Cardio Exercise Bar Chart - {selected_year}', 
            x=0.5, 
            font=dict(
                size=21, 
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        ), 
        yaxis=dict(
            tickfont=dict(size=16), 
            title=dict(
                text="Exercise", 
                font=dict(size=16)
            )
        ), 
        xaxis=dict(
            title=dict(
                text='Count', 
                font=dict(size=16)
            )
        ), 
        legend=dict(visible=False), 
        hovermode='closest', 
        bargap=0.08, 
        bargroupgap=0
    ).update_traces(
        textposition='auto', 
        hovertemplate='<b>Exercise:</b> %{label}<br><b>Count</b>: %{x}<extra></extra>'
    )

    cardio_pie_fig = px.pie(
        df_cardio_counts, 
        names="Cardio Exercise", 
        values='Count'
    ).update_layout(
        title=dict(
            text=f'Cardio Exercise Distribution - {selected_year}',
            x=0.5, 
            font=dict(
                size=21,
                family='Calibri', 
                color='black'
            )
        ), 
        font=dict(
            family='Calibri',
            size=16, 
            color='black'
        )
    ).update_traces(
        rotation=100, 
        texttemplate='%{percent:.1%}', 
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>'
    )
    
    # Prepare table data
    df_indexed = df.reset_index(drop=True).copy()
    # column_order = ['Date', 'Category', 'Exercise', 'Weight']
    # df_indexed = df_indexed[column_order]
    df_indexed.insert(0, '#', df_indexed.index + 1)
    
    table_data = df_indexed.to_dict('records')
    table_columns = [{"name": col, "id": col} for col in df_indexed.columns]
    table_title = f'Fitness Tracker Table - {selected_year}'
    rollup_title = f'Total Gym Days - {selected_year}'
    push_title = f'Total Push Days - {selected_year}'
    pull_title = f'Total Pull Days - {selected_year}'
    leg_title = f'Total Leg Days - {selected_year}'
    bicep_title = f'Total Bicep Days - {selected_year}'
    tricep_title = f'Total Tricep Days - {selected_year}'
    shoulder_title = f'Total Shoulder Days - {selected_year}'
    calisthenics_title = f'Total Calisthenics Days - {selected_year}'
    ab_title = f'Total Ab Days - {selected_year}'
    forearm_title = f'Total Forearm Days - {selected_year}'
    cardio_title = f'Total Cardio Days - {selected_year}'
    year_subtitle = selected_year
    
    return (
        year_subtitle,
        rollup_title,
        total,
        push_title,
        push_days,
        pull_title,
        pull_days,
        leg_title,
        leg_days,
        bicep_title,
        bicep_days,
        tricep_title,
        tricep_days,
        shoulder_title,
        shoulder_days,
        calisthenics_title,
        calisthenics_days,
        ab_title,
        ab_days,
        forearm_title,
        forearm_days,
        cardio_title,
        cardio_days,
        push_fig,
        push_bar_fig,
        push_pie_fig,
        pull_fig,
        pull_bar_fig,
        pull_pie_fig,
        leg_fig,
        leg_bar_fig,
        leg_pie_fig,
        bicep_fig,
        bicep_bar_fig,
        bicep_pie_fig,
        tricep_fig,
        tricep_bar_fig,
        tricep_pie_fig,
        shoulder_fig,
        shoulder_bar_fig,
        shoulder_pie_fig,
        ab_fig,
        ab_bar_fig,
        ab_pie_fig,
        calisthenics_fig,
        calisthenics_bar_fig,
        calisthenics_pie_fig,
        forearm_fig,
        forearm_bar_fig,
        forearm_pie_fig,
        cardio_fig,
        cardio_bar_fig,
        cardio_pie_fig,
        table_title,
        table_data,
        table_columns
    )

print(f"Serving Flask app '{current_file}'! 🚀")

if __name__ == '__main__':
    app.run(debug=
                   True)
                #    False)

# ============================== Save to Excel ========================== #

# updated_path = f'data/{name}_fitness_tracker_cleaned.xlsx'
# data_path = os.path.join(script_dir, updated_path)

# # Create Excel writer object
# with pd.ExcelWriter(data_path, engine='openpyxl') as writer:
#     # Save All Time data
#     df_long.to_excel(writer, sheet_name='All Time', index=False)
    
#     # Dynamically get all available years from Google Sheets
#     all_worksheets = sheet.worksheets()
#     all_years = [ws.title for ws in all_worksheets if ws.title not in ['All Time']]
    
#     # Save individual years
#     for year in all_years:
#         try:
#             # Load data for each year
#             df_year = load_data_for_year(year)
            
#             # Get all date columns
#             date_columns = [col for col in df_year.columns if col not in ['Category', 'Exercise']]
            
#             # Reshape from wide to long format
#             df_year_long = df_year.melt(
#                 id_vars=['Category', 'Exercise'],
#                 value_vars=date_columns,
#                 var_name='Date',
#                 value_name='Weight' 
#             )
            
#             # Clean the data
#             df_year_long['Date'] = pd.to_datetime(df_year_long['Date'], errors='coerce', format='mixed')
#             df_year_long['Weight'] = pd.to_numeric(df_year_long['Weight'], errors='coerce')
#             df_year_long = df_year_long.dropna(subset=['Date', 'Weight'])
#             df_year_long['Category'] = df_year_long['Category'].astype(str).str.strip()
#             df_year_long['Exercise'] = df_year_long['Exercise'].astype(str).str.strip()
#             df_year_long = df_year_long.drop_duplicates(subset=['Category', 'Exercise', 'Date'], keep='first')
#             df_year_long = df_year_long.sort_values('Date').reset_index(drop=True)
            
#             # Save to Excel sheet
#             df_year_long.to_excel(writer, sheet_name=year, index=False)
#             print(f"Saved {year} data to Excel")
#         except Exception as e:
#             print(f"Could not save {year}: {e}")

# print(f"Saved all data to {data_path}")