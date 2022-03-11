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


drf_sidebar_components = html.Div(
    dbc.Accordion(
        [
            dbc.AccordionItem(
                [
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
                    dbc.Button(
                        'Load Data', 
                        id={'type': 'drf-load', 'index': 0,},
                        n_clicks=0, 
                        disabled=True,
                        color="primary",
                    ),
                    html.Br(),

                    dbc.Button(
                        html.I(className="bi bi-play"),
                        # id='reset-val',
                        id={'type': 'drf-play', 'index': 0,},
                        n_clicks=0,
                        disabled=True,
                        color="secondary",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-pause-fill"),
                        id={'type': 'drf-pause', 'index': 0,},
                        n_clicks=0,
                        disabled=True,
                        color="secondary",
                    ),
                    dbc.Button(
                        html.I(className="bi bi-skip-backward"),
                        id={'type': 'drf-rewind', 'index': 0,},
                        n_clicks=0,
                        disabled=True,
                        color="secondary",
                    ),
                ],
                title="DigitalRF Options",
            ),
            dbc.AccordionItem(
                [
                    html.P("Metadata will appear here when you pick a file"),
                ],
                title="Metadata",
                id={
                    'type': 'drf-metadata-accordion', 'index': 0, 
                }
            ),
            dbc.AccordionItem(
                dcc.RadioItems(
                    options=[
                        {'label': 'Log Scale', 'value': 'on'},
                        {'label': 'Linear Scale', 'value': 'off'}
                    ],
                    value='on',
                    id={
                        'type': 'radio-log-scale', 'index': 0, 
                    },
                    labelStyle={"verticalAlign": "middle"},
                    className="plot-display-radio-items",
                ),
                title="Graph settings",
            ),
        ],
        id="stream-accordion",
        # flush=True,
        start_collapsed=False,
    )
)
