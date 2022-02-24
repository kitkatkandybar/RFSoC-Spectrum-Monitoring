import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

 
# create radio option components
drf_sidebar_radio = html.Div([

        html.P(
                "Log Scale:",
                style={"font-weight": "bold", "margin-bottom": "0px"},
                className="plot-display-text",
            ),
         html.Div(
        [

            dcc.RadioItems(

                    options=[
                        {'label': 'Log Scale', 'value': 'on'},
                        {'label': 'Linear Scale', 'value': 'off'}
                    ],
                value='off',
                # id=f"radio-log-scale",
                id={
                    'type': 'radio-log-scale', 'index': 0, 
                },
                labelStyle={"verticalAlign": "middle"},
                className="plot-display-radio-items",
            )
        ],
        className="radio-item-div",
    )
])


drf_sidebar_components = html.Div([
        dcc.Input(
            id="drf-path", 
            type="text",
            value="C:/Users/yanag/openradar/openradar_antennas_wb_hf/",
            style={'width': '100%'}
        ),
        dbc.Button(
            'Choose input directory', 
            id='input-dir-button', 
            n_clicks=0,
            color="primary",
        ),
        html.Br(),
        html.Div(id='drf-err'),
        dcc.Loading(
            id="channel-loading",
            children=[
                html.Div(id='channel-div', style={'width': '100%'}),
                
            ],
            type="circle",
        ),
        
        html.Div(id='sample-div', style={'width': '100%'},),
        html.Div(id='bins-div', style={'width': '100%'},),
        html.Div(id='metadata-output'),
        dbc.Button(
            'Load Data', 
            id='load-val', 
            n_clicks=0, 
            disabled=True,
            color="primary",
        ),
        dbc.Button(
            'Playback data from beginning', 
            id='reset-val',
            n_clicks=0,
            disabled=True,
            color="secondary",
        ),
        drf_sidebar_radio,
])
