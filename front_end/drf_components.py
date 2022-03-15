import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

 

drf_form_modal = html.Div(
    [
        dbc.Button("Select Digital RF Data", id="open-modal-button", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Digital RF Options Form")),
                dbc.ModalBody([
                    dbc.Label("Digital RF Directory", html_for="drf-path"),
                    dbc.Row([
                        dbc.Col(
                            dcc.Input(
                                id="drf-path", 
                                type="text",
                                value="C:/Users/yanag/openradar/openradar_antennas_wb_hf/",
                                style={'width': '100%'}
                            ),
                            className="me-3",
                            # width=6,
                        ),
                        dbc.Col(
                               dbc.Button(
                                'Select', 
                                id='input-dir-button', 
                                n_clicks=0,
                                color="primary",
                            ),
                            width="auto",
                        ),
                        
                    ]),
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

                    ]),
                dbc.ModalFooter([
                    dbc.Button(
                        'Load Data', 
                        id={'type': 'drf-load', 'index': 0,},
                        n_clicks=0, 
                        disabled=True,
                        color="primary",
                    ),
                    dbc.Button(
                        "Close", id="close-modal-button", className="ms-auto", n_clicks=0
                    )
                ]),
            ],
            id="drf-form-modal",
            is_open=False,
            size="lg",
        ),
    ]
)

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
                    drf_form_modal,
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
                [
                    dbc.Label("Y axis scale", html_for="radio-log-scale"),
                    dcc.RadioItems(
                        options=[
                            {'label': 'Log Scale', 'value': 'on'},
                            {'label': 'Linear Scale', 'value': 'off'}
                        ],
                        value='on',
                        id={
                            'type': 'radio-log-scale', 'index': 0, 
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
                            'type': 'specgram-color-dropdown', 'index': 0, 
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
