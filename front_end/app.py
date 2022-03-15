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
                        
                        dcc.Graph(
                            id='specgram-graph',
                            figure=cfg.sa.spectrogram.get_plot()
                        ),

                    ],
                ),

            ], width=True,),
        ]),
        dcc.Store(data=session_id, id='session-id'),
        dcc.Store(id='request-id', data=-1),
        dcc.Store(id='graph_data_index', data=0,),
        dcc.Store(id='stream-data'),
        dcc.Store(id='drf-data'),
        dcc.Store(id='drf-data-finished', data="False"),
        dcc.Store(id='placeholder'),

    ], fluid=True)

app.layout = serve_layout()


@app.callback(dash.Output('sidebar-content', 'children'),
              dash.Input("content-tabs", 'value'))
def render_tab_content(tab):
    cfg.sa.spectrogram.clear_data()
    cfg.sa.spec.data        = []
    if cfg.spec_datas:
        cfg.spec_datas = {}

    if tab == 'content-tab-1':
        print("tab 1")
        # TODO: DISABLE ANY STREAMING COMPONENTS
        return drf_sidebar_components
    elif tab == 'content-tab-2':
        print("tab 2")

        return stream_sidebar_components



@app.callback(dash.Output('spectrum-graph', 'figure'),
              dash.Input('stream-data', 'data'),
              dash.Input('drf-data', 'data'),
              dash.Input({'type': 'radio-log-scale', 'index': dash.ALL,}, 'value'),
              dash.Input({'type': 'stream-metadata-accordion', 'index': dash.ALL,}, 'children'),
              dash.Input('request-id', 'data'),

              )
def update_spectrum_graph(stream_data, drf_data, log_scale, stream_metadata, req_id):
    """ update the spectrum graph with new data, every time
    the Interval component fires"""

    ctx = dash.callback_context
    if not ctx.triggered: # or not cfg.spec_datas:
        return cfg.sa.plot

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # print("called update spectrum graph")

    if prop_id == "stream-data":
        cfg.sa.spec.show_data()
        cfg.sa.spec.y_autorange = False
        d = np.asarray(stream_data)
        if log_scale[0] == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        cfg.sa.spec.data        = d
        return cfg.sa.plot
    elif prop_id == "drf-data":
        d = np.asarray(drf_data)
        if log_scale[0] == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        cfg.sa.spec.data        = d
        return cfg.sa.plot

    else:
        # log scale option has been modified
        if log_scale and log_scale[0] == 'on':
            cfg.sa.spec.ylabel = "Amplitude (dB)" 
            if cfg.spec_datas:
                cfg.sa.spec.yrange = (10.0 * np.log10(cfg.spec_datas['metadata']['y_min'] + 1e-12) - 3, 
                                      10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) + 10)
                cfg.sa.spec.data   =  10.0 * np.log10(cfg.sa.spec.data + 1e-12)  
            
        else:
            cfg.sa.spec.ylabel = "Amplitude" 
            if cfg.spec_datas:
                cfg.sa.spec.yrange = (cfg.spec_datas['metadata']['y_min'], cfg.spec_datas['metadata']['y_max'])
 



    return cfg.sa.plot




@app.callback(dash.Output('specgram-graph', 'figure'),
              dash.Input('stream-data', 'data'),
              dash.Input('drf-data', 'data'),
              dash.Input({'type': 'radio-log-scale', 'index': dash.ALL,}, 'value'),
              dash.Input({'type': 'stream-metadata-accordion', 'index': dash.ALL,}, 'children'),
              dash.Input('request-id', 'data'),

              )

def update_specgram_graph(stream_data, drf_data, log_scale, stream_metadata, req_id):
    """ update the spectogram plot with new data, every time
    the Interval component fires"""
    ctx = dash.callback_context
    if not ctx.triggered: # or not cfg.spec_datas:
        return cfg.sa.spectrogram.get_plot()

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]


    if prop_id == "stream-data":
        d = np.asarray(stream_data)
        if log_scale[0] == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        cfg.sa.spectrogram.data = d
        return cfg.sa.spectrogram.get_plot()
    elif prop_id == "drf-data":
        d = np.asarray(drf_data)
        if log_scale[0] == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        cfg.sa.spectrogram.data = d

    else:
        # log scale option has been modified
        if log_scale and log_scale[0] == 'on':
            cfg.sa.spectrogram.zlabel =  "Power (dB)"
            if cfg.spec_datas:
                cfg.sa.spectrogram.zmin   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_min']+ 1e-12) - 3
                cfg.sa.spectrogram.zmax   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) + 10
            
        else:
            cfg.sa.spectrogram.zlabel = "Power"
            if cfg.spec_datas:
                cfg.sa.spectrogram.zmin   = cfg.spec_datas['metadata']['y_min']
                cfg.sa.spectrogram.zmax   = cfg.spec_datas['metadata']['y_max']
      

    return cfg.sa.spectrogram.get_plot()






if __name__ == '__main__':
    # app.run_server(debug=True, processes=6)
    parser = argparse.ArgumentParser()
    parser.add_argument('--cfg', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml"), help='Config file for this application')

    args = parser.parse_args()
    with open(args.cfg, 'r') as f:
        cfg_data = yaml.safe_load(f)

    # initialize redis instance based on cfg params
    cfg.redis_instance = redis.Redis(host=cfg_data['redis']['host'], port=cfg_data['redis']['port'], db=0)

    app.run_server(debug=True)
