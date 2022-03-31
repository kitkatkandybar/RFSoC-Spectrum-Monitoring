import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

from shared_components import get_graph_settings, get_spectrum_graph_settings, get_specgram_graph_settings

 
DRF_TAB_IDX = 0

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
                                value="",
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
                    html.Div(id='int-mod-div', style={'width': '100%'},),
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
                    html.Hr(),
                    dbc.Label("Playback controls", html_for="drf-path"),
                    html.Br(),
                    dbc.Button(
                        html.I(className="bi bi-play"),
                        id={'type': 'drf-play', 'index': 0,},
                        n_clicks=0,
                        disabled=True,
                        color="primary",
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
                        color="primary",
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
                get_graph_settings(DRF_TAB_IDX),
                title="Graph settings",
            ),
            dbc.AccordionItem(
                get_spectrum_graph_settings(DRF_TAB_IDX),
                title="Spectrum graph settings",
            ),
            dbc.AccordionItem(
               get_specgram_graph_settings(DRF_TAB_IDX),
                title="Spectrogram graph settings",
            ),
        ],
        id="stream-accordion",
        # flush=True,
        start_collapsed=False,
    )
)
