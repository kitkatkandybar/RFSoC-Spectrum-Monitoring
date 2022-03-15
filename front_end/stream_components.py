import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc



stream_sidebar_components = html.Div(
    dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    html.H4("Choose the stream:"),
                    html.Div(id='stream-picker-div', children=[
                    dcc.Dropdown(
                        id={
                            'type': 'stream-picker', 'index': 0, 
                        }
                    ),]
                    ),
                    dbc.Button(
                        'Play stream data', 
                        id={
                            'type': 'play-stream-data', 'index': 0, 
                        },
                        n_clicks=0, 
                        disabled=True,
                        color="primary",
                    ),
                    dbc.Button(
                        'Pause', 
                        id={
                            'type': 'pause-stream-data', 'index': 0, 
                        },
                        n_clicks=0, 
                        disabled=True,
                        color="secondary",
                    ),
                ],
                title="Stream Options",
            ),
            dbc.AccordionItem(
                [
                    html.P("Metadata will appear here when you pick a stream"),
                ],
                title="Metadata",
                id={
                    'type': 'stream-metadata-accordion', 'index': 0, 
                }
            ),
            dbc.AccordionItem(
                 [
                    dbc.Label("Y axis scale", html_for="radio-log-scale"),
                    dcc.RadioItems(
                        options=[
                            {'label': 'Log Scale', 'value': 'on'},
                            {'label': 'Linear Scale', 'value': 'off'}
                        ],
                        value='on',
                        id={
                            'type': 'radio-log-scale', 'index': 1, 
                        },
                        labelStyle={"verticalAlign": "middle", 'padding-right': '10px'},
                        className="plot-display-radio-items",
                    ),
                    dbc.Label("Spectrogram Colorscheme", html_for="specgram-color-dropdown"),
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
                            'type': 'specgram-color-dropdown', 'index': 1, 
                        },
                        searchable=False,
                        clearable=False
                    ),
                ],
                title="Graph settings",
            ),
        ],
        id="stream-accordion",
        # flush=True,
        start_collapsed=False,
    )
)