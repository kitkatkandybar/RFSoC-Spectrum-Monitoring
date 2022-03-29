import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

from shared_components import get_graph_settings, get_spectrum_graph_settings, get_specgram_graph_settings

STREAM_TAB_IDX = 1

download_modal = html.Div(
    [
        dbc.Button("Download Data From Board", id="open-download-modal-button", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Download Data From Board")),
                dbc.ModalBody([
                    dbc.Label("Choose board", html_for="drf-path"),
            

                    ]),
                dbc.ModalFooter([
                    dbc.Button(
                        'Download Data', 
                        id={'type': 'download-button', 'index': 0,},
                        n_clicks=0, 
                        disabled=True,
                        color="primary",
                    ),
                    dbc.Button(
                        "Close", id="close-download-modal-button", className="ms-auto", n_clicks=0
                    )
                ]),
            ],
            id="download-modal",
            is_open=False,
            size="lg",
        ),
    ]
)


stream_sidebar_components = html.Div(
    dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    # html.H4("Choose the stream:"),
                    dbc.Label("Stream Name", html_for="stream-picker-div"),
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
                get_graph_settings(STREAM_TAB_IDX),
                title="Graph settings",
            ),
            dbc.AccordionItem(
                get_spectrum_graph_settings(STREAM_TAB_IDX),
                title="Spectrum graph settings",
            ),
            dbc.AccordionItem(
               get_specgram_graph_settings(STREAM_TAB_IDX),
                title="Spectrogram graph settings",
            ),
            dbc.AccordionItem(
                [download_modal],
                title="Download options",
            ),
        ],
        id="stream-accordion",
        # flush=True,
        start_collapsed=False,
    )
)