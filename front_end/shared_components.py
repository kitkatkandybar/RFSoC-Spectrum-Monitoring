from dash import dcc
from dash import html
import dash_bootstrap_components as dbc


def get_graph_settings(id_num):
	return    [
                    dbc.Label("Y axis scale", html_for="radio-log-scale"),
                    dcc.RadioItems(
                        options=[
                            {'label': 'Log Scale', 'value': 'on'},
                            {'label': 'Linear Scale', 'value': 'off'}
                        ],
                        value='on',
                        id={
                            'type': 'radio-log-scale', 'index': id_num, 
                        },
                        labelStyle={"verticalAlign": "middle", 'padding-right': '10px'},
                        className="plot-display-radio-items",
                    ),
                    html.Hr(),
                    
                    dbc.Label("Display maximum", html_for="radio-display-max"),
                    dcc.RadioItems(
                        options=[
                            {'label': 'On', 'value': 'on'},
                            {'label': 'Off', 'value': 'off'}
                        ],
                        value='off',
                        id={
                            'type': 'radio-display-max', 'index': id_num, 
                        },
                        labelStyle={"verticalAlign": "middle", 'padding-right': '10px'},
                        className="plot-display-radio-items",
                    ),
                    html.Hr(),

                    dbc.Label("Display minimum", html_for="radio-display-min"),
                    dcc.RadioItems(
                        options=[
                            {'label': 'On', 'value': 'on'},
                            {'label': 'Off', 'value': 'off'}
                        ],
                        value='off',
                        id={
                            'type': 'radio-display-min', 'index': id_num, 
                        },
                        labelStyle={"verticalAlign": "middle", 'padding-right': '10px'},
                        className="plot-display-radio-items",
                    ),
                    html.Hr(),
                    
                    dbc.Label("Spectrogram colorscheme", html_for="specgram-color-dropdown"),
                    dcc.Dropdown(
                        options=[
                            {'label': 'viridis', 'value': 'viridis',},    
                            {'label': 'inferno', 'value': 'inferno',},    
                            {'label': 'magma',   'value': 'magma',  },    
                            {'label': 'cividis', 'value': 'cividis',},    
                            {'label': 'jet',     'value': 'jet',    },   
                        ],
                        value='jet',
                        id={
                            'type': 'specgram-color-dropdown', 'index': id_num, 
                        },
                        searchable=False,
                        clearable=False
                    ),
                ]