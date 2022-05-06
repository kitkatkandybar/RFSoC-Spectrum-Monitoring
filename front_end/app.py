"""
This file represents the core interface of the web application -
running it starts the web app.

It also defines the layout and functionality of the app.

"""

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import re
import argparse
import os.path
import logging
logger = logging.getLogger(__name__)

import yaml
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import numpy as np
import uuid
import redis

from drf_components import *
import drf_callbacks
from stream_components import *
import stream_callbacks
import shared_callbacks
import config as cfg


# create a Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)



def serve_layout():
    session_id = str(uuid.uuid4())

    return dbc.Container([
        dbc.Row(
            [
            dbc.Col(
                [
                    html.H1(children='Spectrum Monitoring Dashboard'),
                ],
                width=True,
            ),
        ]),
        html.Hr(),
        dbc.Row(dcc.Tabs(id="content-tabs", value='content-tab-1', 
            children=[
                dcc.Tab(label='Digital RF', value='content-tab-1'),
                dcc.Tab(label='Streaming', value='content-tab-2'),
        ])),
        dbc.Row([
            dbc.Col(html.Div(id='sidebar-content'), width=3),
            dbc.Col([
                html.Div(
                    className="graph-section",
                    children=[
                        dcc.Graph(
                            id='spectrum-graph',
                            figure=cfg.sa.plot
                        ),
                         dcc.Graph(
                            id='specgram-graph',
                            figure=cfg.sa.spectrogram.get_plot()
                        ),
                    ],
                ),

            ], width=True,),
        ]),
        # intervals for updating graphs
        dcc.Interval(
            id='drf-interval',
            interval=1*150, # in milliseconds
            n_intervals=0,
            disabled=True,
        ),
        dcc.Interval(
            id='stream-graph-interval',
            interval=200, # in milliseconds
            n_intervals=0,
            disabled=True,
        ),
        # Store values for storing data between callbacks
        dcc.Store(id='session-id', data=session_id),
        dcc.Store(id='request-id', data=-1),
        dcc.Store(id='graph_data_index', data=0,),
        dcc.Store(id='stream-data'),
        dcc.Store(id='drf-data'),
        dcc.Store(id='drf-data-finished', data="False"),
        dcc.Store(id='spectrum-y-min', data=-1),
        dcc.Store(id='spectrum-y-max', data=-4),
        dcc.Store(id='drf-n-samples', data=0),
        dcc.Store(id='placeholder'),
        dcc.Store(id='download-placeholder'),
        dcc.Download(id="download-board-data"),

    ], fluid=True)

app.layout = serve_layout()


@app.callback(
    dash.Output('sidebar-content', 'children'),
    dash.Input("content-tabs", 'value'),
)
def render_tab_content(tab):
    """ Switches sidebar content as appropriate when the DigitalRF or Streaming tab is selected """

    # clear graph data
    cfg.sa.spectrogram.clear_data()
    cfg.sa.spec.data = np.array([])
    if cfg.spec_datas:
        cfg.spec_datas = {}

    if tab == 'content-tab-1':
        print("Switching to DigitalRF tab")
        # TODO: DISABLE ANY STREAMING COMPONENTS
        return drf_sidebar_components

    elif tab == 'content-tab-2':
        print("Switching to Streaming tab")

        return stream_sidebar_components

@app.callback(
    dash.Output('spectrum-graph', 'figure'),
    dash.Input('stream-data', 'data'),
    dash.Input('drf-data', 'data'),
    dash.Input({'type': 'spectrum-radio-log-scale', 'index': dash.ALL,}, 'value'),
    dash.Input({'type': 'radio-display-max', 'index': dash.ALL,}, 'value'),
    dash.Input({'type': 'radio-display-min', 'index': dash.ALL,}, 'value'),
    dash.Input({'type': 'stream-metadata-accordion', 'index': dash.ALL,}, 'children'),
    dash.Input('request-id', 'data'),
    dash.Input({'type': 'spectrum-y-min-input', 'index': dash.ALL,}, 'value'),
    dash.Input({'type': 'spectrum-y-max-input', 'index': dash.ALL,}, 'value'),
)
def update_spectrum_graph(
        stream_data, drf_data, log_scale, 
        display_max, display_min, stream_metadata, 
        req_id, y_min_val, y_max_val):
    """ 
    Updates the Spectrum graph with new data, every time
    the Interval component fires. Also handles user interaction options with the graph,
    such as adjusting the y axis scales, tracking max/min points, and toggling the log/linear scaling 
    """

    ctx = dash.callback_context
    if not ctx.triggered: # or not cfg.spec_datas:
        return cfg.sa.plot

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Stream data has been updated
    if prop_id == "stream-data": 
        cfg.sa.spec.show_data()
        # cfg.sa.spec.y_autorange = False
        d = np.asarray(stream_data)
        # if log_scale[0] == 'on':
        #     d = 10.0 * np.log10(d + 1e-12)
        if log_scale[0] == 'off':
            d = np.power(10, d)
        cfg.sa.spec.data = d
        return cfg.sa.plot

    # Digital RF playback data has been updated
    elif prop_id == "drf-data":
        d = np.asarray(drf_data)
        if log_scale[0] == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        cfg.sa.spec.data = d
        return cfg.sa.plot

    # Y-axis minimum value has been updated
    elif "spectrum-y-min-input" in prop_id:
        cfg.sa.spec.yrange = (y_min_val[0], cfg.sa.spec.yrange[1])

    # Y-axis maximum value has been updated
    elif "spectrum-y-max-input" in prop_id:
        cfg.sa.spec.yrange = (cfg.sa.spec.yrange[0], y_max_val[0])

    # "Display maximum value" toggle has been updated
    elif "max" in prop_id:
        if display_max[0] == 'on':
            cfg.sa.spec.display_max = True
        else:
            cfg.sa.spec.display_max = False

    # "Display minimum value" toggle has been updated
    elif "min" in prop_id:
        if display_min[0] == 'on':
            cfg.sa.spec.display_min = True
        else:
            cfg.sa.spec.display_min = False

    # log scale option has been modified
    else:
        if log_scale and log_scale[0] == 'on':
            cfg.sa.spec.ylabel = "Amplitude (dB)" 
            if cfg.spec_datas:
                cfg.sa.spec.yrange = (10.0 * np.log10(cfg.spec_datas['metadata']['y_min'] + 1e-12) - 3, 
                                      10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) + 10)
                # cfg.sa.spec.data   =  10.0 * np.log10(cfg.sa.spec.data + 1e-12)  
            
        else:
            cfg.sa.spec.ylabel = "Amplitude" 
            if cfg.spec_datas:
                cfg.sa.spec.yrange = (cfg.spec_datas['metadata']['y_min'], cfg.spec_datas['metadata']['y_max'])
 
    return cfg.sa.plot




@app.callback(
    dash.Output('specgram-graph', 'figure'),
    dash.Input('stream-data', 'data'),
    dash.Input('drf-data', 'data'),
    dash.Input({'type': 'specgram-radio-log-scale', 'index': dash.ALL,}, 'value'),
    dash.Input({'type': 'specgram-color-dropdown', 'index': dash.ALL,}, 'value'),
    dash.Input({'type': 'stream-metadata-accordion', 'index': dash.ALL,}, 'children'),
    dash.Input('request-id', 'data'),
    dash.Input({'type': 'specgram-y-min-input', 'index': dash.ALL,}, 'value'),
    dash.Input({'type': 'specgram-y-max-input', 'index': dash.ALL,}, 'value'),
)
def update_specgram_graph(
        stream_data, drf_data, log_scale, 
        color,  stream_metadata, req_id, 
        y_min_val, y_max_val):
    """ 
    Updates the Spectogram graph with new data, every time
    the Interval component fires. Also handles user interaction options with the graph,
    such as adjusting the axis scales, changing the colorscale of the grph, 
    and toggling the log/linear scaling 
    """

    ctx = dash.callback_context
    if not ctx.triggered: # or not cfg.spec_datas:
        return cfg.sa.spectrogram.get_plot()

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Stream data has been updated
    if prop_id == "stream-data":
        d = np.asarray(stream_data)
        # if log_scale[0] == 'on':
        #     d = 10.0 * np.log10(d + 1e-12)
        if log_scale[0] == 'off':
            d = np.power(10, d)
        cfg.sa.spectrogram.data = d
        
        return cfg.sa.spectrogram.get_plot()

    # Digital RF playback data has been updated
    elif prop_id == "drf-data":
        d = np.asarray(drf_data)
        if log_scale[0] == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        cfg.sa.spectrogram.data = d

    # color scale has been updated
    elif "color" in prop_id:
        print("Changing color to: {}", color[0])
        cfg.sa.spectrogram.cmap = color[0]

    # Y-axis minimum value has been updated
    elif "specgram-y-min-input" in prop_id:
        cfg.sa.spectrogram.zmin = y_min_val[0]

    # Y-axis maximum value has been updated
    elif "specgram-y-max-input" in prop_id:
        cfg.sa.spectrogram.zmax = y_max_val[0]

    # log scale option has been modified
    else:
        if log_scale and log_scale[0] == 'on':
            cfg.sa.spectrogram.zlabel =  "Power (dB)"
            if cfg.spec_datas:
                cfg.sa.spectrogram.zmin   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_min'] + 1e-12) - 3
                cfg.sa.spectrogram.zmax   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) + 10
            
        else:
            cfg.sa.spectrogram.zlabel = "Power"
            if cfg.spec_datas:
                cfg.sa.spectrogram.zmin   = cfg.spec_datas['metadata']['y_min']
                cfg.sa.spectrogram.zmax   = cfg.spec_datas['metadata']['y_max']
      

    return cfg.sa.spectrogram.get_plot()


if __name__ == '__main__':
    # initialize logger
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--cfg', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml"), help='Config file for this application')
    args = parser.parse_args()

    # get config values
    with open(args.cfg, 'r') as f:
        cfg_data = yaml.safe_load(f)

    # initialize redis instance based on cfg params
    print(f"Connecting to redis server at {cfg_data['redis']['host']}:{cfg_data['redis']['port']}...")
    cfg.redis_instance = redis.Redis(host=cfg_data['redis']['host'], port=cfg_data['redis']['port'], db=0, password=cfg_data['redis']['password'])

    # initialize host/port of Dash app based on cfg params
    host = cfg_data['dash']['host'] if cfg_data['dash']['host'] else None
    port = cfg_data['dash']['port'] if cfg_data['dash']['port'] else None



    # run app
    if host:
        if port:
            app.run_server(debug=True, host=host, port=port)
        else:
            app.run_server(debug=True, host=host)
    elif port:
        app.run_server(debug=True, port=port)
    else:
        app.run_server(debug=True)
