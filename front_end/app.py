"""
This file represents the core interface of the web application -
running it starts the web app.

It also defines the layout and functionality of the app.

"""

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import re
import time
import json

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import numpy as np
import uuid

from flask_caching import Cache

import redis



from drf_components import *
import drf_callbacks

from stream_components import *
import stream_callbacks

# from config import cfg.data_queue, cfg.data_q_idx, cfg.sa, cfg.spec_datas, cfg.redis_instance, cfg.pubsub
import config as cfg


# create a Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY], suppress_callback_exceptions=True)
# cache = Cache(app.server, config={
#     'CACHE_TYPE': 'redis',
#     'CACHE_REDIS_URL': 'redis://localhost:6379',
#     # Note that filesystem cache doesn't work on systems with ephemeral
#     # filesystems like Heroku.
#     # 'CACHE_TYPE': 'filesystem',
#     'CACHE_DIR': 'cache-directory',

#     # should be equal to maximum number of users on the app at a single time
#     # higher numbers will store more data in the filesystem / redis cache
#     'CACHE_THRESHOLD': 200
# })




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
                                id='graph-interval',
                                interval=1*150, # in milliseconds
                                n_intervals=0,
                                # max_intervals=100,
                                disabled=True,
                            ),
                        dcc.Interval(
                                id='stream-interval',
                                interval=1000, # in milliseconds
                                n_intervals=0,
                                # max_intervals=100,
                                disabled=True,
                            ),
                        dcc.Interval(
                                id='stream-graph-interval',
                                interval=1*150, # in milliseconds
                                n_intervals=0,
                                # max_intervals=100,
                                disabled=True,
                            ),
                        
                        dcc.Graph(
                            id='specgram-graph',
                            figure=cfg.sa.spectrogram.get_plot()
                        ),
                        html.P(id='placeholder', n_clicks=0)

                    ],
                ),

            ], width=True,),
        ]),
        dcc.Store(data=session_id, id='session-id'),
        dcc.Store(id='metadata'),
        dcc.Store(id='request-id'),
        dcc.Store(id='spec-data'),
        html.Div(id='reading-stream-graph-interval-placeholder', n_clicks=0,),
        html.Div(id='spectrum-graph-interval-placeholder', n_clicks=0,),
        html.Div(id='reset-button-graph-interval-placeholder', n_clicks=0,),
        html.Div(id='reset-button-placeholder', n_clicks=0,),
        dcc.Store(id='graph_data_index', data=0,),
        dcc.Store(id='stream-last-id', data=-1,),
        dcc.Store(id='stream-data'),

    ], fluid=True)

app.layout = serve_layout()


# def get_dataframe(session_id):
#     @cache.memoize()
#     def query_and_serialize_data(session_id):
#         # expensive or user/session-unique data processing step goes here

#         # simulate a user/session-unique data processing step by generating
#         # data that is dependent on time
#         now = datetime.datetime.now()

#         # simulate an expensive data processing task by sleeping
#         time.sleep(3)

#         df = pd.DataFrame({
#             'time': [
#                 str(now - datetime.timedelta(seconds=15)),
#                 str(now - datetime.timedelta(seconds=10)),
#                 str(now - datetime.timedelta(seconds=5)),
#                 str(now)
#             ],
#             'values': ['a', 'b', 'a', 'c']
#         })
#         return df.to_json()

#     return pd.read_json(query_and_serialize_data(session_id))

# def get_metadata(session_id, request_id):
#     @cache.memoize()
#     def query_and_serialize_metadata(session_id, request_id):
#         pass

#     return json.loads(query_and_serialize_metadata(session_id, request_id))


# app.clientside_callback(
#     """
#     function(largeValue1, largeValue2) {
#         return someTransform(largeValue1, largeValue2);
#     }
#     """,
#     dash.Output('out-component', 'value'),
#     dash.Input('in-component1', 'value'),
#     dash.Input('in-component2', 'value')
# )


@app.callback(dash.Output('sidebar-content', 'children'),
              dash.Input("content-tabs", 'value'))
def render_tab_content(tab):
    if tab == 'content-tab-1':
        print("tab 1")
        # TODO: DISABLE ANY STREAMING COMPONENTS
        return drf_sidebar_components
    elif tab == 'content-tab-2':
        print("tab 2")

        return stream_sidebar_components



@app.callback(
    dash.Output('graph-interval', 'disabled'),
    dash.Input('reading-stream-graph-interval-placeholder', 'n_clicks'),
    dash.Input('spectrum-graph-interval-placeholder', 'n_clicks'),
    dash.Input('reset-button-graph-interval-placeholder', 'n_clicks'),
)
def update_graph_interval(reading_interval, spectrum_interval, reset_button_interval):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if prop_id == "reading-stream-graph-interval-placeholder":
        disabled = not bool(reading_interval)
        if not disabled:
            cfg.sa.spec.show_data()

    if prop_id == "spectrum-graph-interval-placeholder":
        disabled = not bool(spectrum_interval)

    if prop_id == 'reset-button-graph-interval-placeholder':
        disabled = not bool(reset_button_interval)

    print(f'Graph interval component is disabled: {disabled}')

    return disabled


@app.callback(
            dash.Output('spectrum-graph-interval-placeholder', 'n_clicks'),
            dash.Output('graph_data_index', 'data'),
            dash.Input('graph-interval', 'n_intervals'))
def handle_graph_interval(n):
    if n < 1: raise dash.exceptions.PreventUpdate
    # global cfg.data_q_idx
    print(f"handle_graph_interval: cfg.data_q_idx: {cfg.data_q_idx}, data queue len: {len(cfg.data_queue)}")
    if cfg.data_q_idx < len(cfg.data_queue):
        print(f"\tboop: cfg.data_q_idx: {cfg.data_q_idx}")

        cfg.data_q_idx += 1
        return dash.no_update, cfg.data_q_idx-1
    elif len(cfg.data_queue) > 0:
        print("Reached the end of the data queue, disabling graph interval")
        return 0, dash.no_update # disable future updates to graph

    raise dash.exceptions.PreventUpdate


@app.callback(dash.Output('spectrum-graph', 'figure'),
              dash.Input('graph_data_index', 'data'),
              dash.Input('stream-data', 'data'),
              dash.Input({'type': 'radio-log-scale', 'index': dash.ALL,}, 'value'),
              )
def update_spectrum_graph(n, stream_data, log_scale):
    """ update the spectrum graph with new data, every time
    the Interval component fires"""

    ctx = dash.callback_context
    if not ctx.triggered: # or not cfg.spec_datas:
        return cfg.sa.plot

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print("called update spectrum graph")
    if prop_id == "graph_data_index": # interval component has fired
        if n == 0:
            if log_scale[0] == 'on':
                cfg.sa.spec.ylabel = "Amplitude (dB)" 
                cfg.sa.spec.yrange = (10.0 * np.log10(cfg.spec_datas['metadata']['y_min'] + 1e-12) - 3, 
                                    10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) + 10)
                cfg.sa.spec.data   =  10.0 * np.log10(cfg.sa.spec.data + 1e-12)  
                
            else:
                cfg.sa.spec.ylabel = "Amplitude" 
                cfg.sa.spec.yrange = (cfg.spec_datas['metadata']['y_min'], cfg.spec_datas['metadata']['y_max'])
        cfg.sa.spec.y_autorange = False
        if n < len(cfg.data_queue):
            d = np.asarray(cfg.data_queue[n])
            if log_scale[0] == 'on':
                d = 10.0 * np.log10(d + 1e-12)
            cfg.sa.spec.data        = d
            return cfg.sa.plot
        else:
            print(f"update_spectrum_graph: gone past the length of the data queue? cfg.data_queue len: {len(cfg.data_queue)}, idx: {n}")
            raise dash.exceptions.PreventUpdate
    elif prop_id == "stream-data":
        cfg.sa.spec.show_data()
        cfg.sa.spec.y_autorange = False
        d = np.asarray(stream_data)
        print(f"x range: {cfg.sa.spec._range}")
        if log_scale[0] == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        cfg.sa.spec.data        = d
        return cfg.sa.plot

    else:
        # log scale option has been modified
        
        y_min = float(cfg.spec_datas['metadata']['y_min']) if cfg.spec_datas else None
        y_max = float(cfg.spec_datas['metadata']['y_max']) if cfg.spec_datas else None
        print(f"modifying log scale, ymin: {y_min}, ymax: {y_max}")
        if '0' in prop_id:
            if log_scale and log_scale[0] == 'on':
                cfg.sa.spec.ylabel = "Amplitude (dB)" 
                cfg.sa.spec.yrange = (10.0 * np.log10(y_min + 1e-12) - 3, 
                                      10.0 * np.log10(y_max + 1e-12) + 10)
                cfg.sa.spec.data   =  10.0 * np.log10(cfg.sa.spec.data + 1e-12)  
                
            else:
                cfg.sa.spec.ylabel = "Amplitude" 
                if cfg.spec_datas:
                    cfg.sa.spec.yrange = (cfg.spec_datas['metadata']['y_min'], cfg.spec_datas['metadata']['y_max'])
        else:
            if log_scale and log_scale[0] == 'on':
                cfg.sa.spec.ylabel = "Amplitude (dB)"
                cfg.sa.spec.yrange = (10.0 * np.log10(y_min + 1e-12) - 3, 
                                      10.0 * np.log10(y_max + 1e-12) + 10)
                cfg.sa.spec.data   =  10.0 * np.log10(cfg.sa.spec.data + 1e-12)  
            else:
                cfg.sa.spec.ylabel = "Amplitude" 
                if cfg.spec_datas:
                    cfg.sa.spec.yrange = (y_min,y_max)
        print(f"Changing yrange to : {cfg.sa.spec.yrange}")



    return cfg.sa.plot




@app.callback(dash.Output('specgram-graph', 'figure'),
              dash.Input('graph_data_index', 'data'),
              dash.Input('stream-data', 'data'),
              dash.Input({'type': 'radio-log-scale', 'index': dash.ALL,}, 'value'))
def update_specgram_graph(n, stream_data, log_scale):
    """ update the spectogram plot with new data, every time
    the Interval component fires"""
    ctx = dash.callback_context
    if not ctx.triggered: # or not cfg.spec_datas:
        return cfg.sa.spectrogram.get_plot()

    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if prop_id == "graph_data_index": # interval component has fired
        print(f"update_specgram_graph: cfg.data_queue len: {len(cfg.data_queue)}, idx: {n}")

        if n == 1:
            if log_scale[0] == 'on': # log scale option has changed
                cfg.sa.spectrogram.zlabel =  "Power (dB)"
                cfg.sa.spectrogram.zmin   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_min'] + 1e-12) - 3
                cfg.sa.spectrogram.zmax   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) + 10
                
            else:
                cfg.sa.spectrogram.zlabel = "Power"
                if cfg.spec_datas:
                    cfg.sa.spectrogram.zmin   = cfg.spec_datas['metadata']['y_min']
                    cfg.sa.spectrogram.zmax   = cfg.spec_datas['metadata']['y_max']


        if n < len(cfg.data_queue):
            d = np.asarray(cfg.data_queue[n])
            if log_scale[0] == 'on':
                d = 10.0 * np.log10(d + 1e-12)

            cfg.sa.spectrogram.data = d
            return cfg.sa.spectrogram.get_plot()
        else:
            return dash.no_update
    elif prop_id == "stream-data":
        d = np.asarray(stream_data)
        print(f"x range: {cfg.sa.spec._range}")
        if log_scale[0] == 'on':
            d = 10.0 * np.log10(d + 1e-12)
        cfg.sa.spectrogram.data = d
        return cfg.sa.spectrogram.get_plot()
    # else:
    #     if log_scale and log_scale[0] == 'on': # log scale option has changed
    #         cfg.sa.spectrogram.zlabel =  "Power (dB)"
    #         cfg.sa.spectrogram.zmin   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_min']+ 1e-12) - 3
    #         cfg.sa.spectrogram.zmax   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) + 10
            
    #     else:
    #         cfg.sa.spectrogram.zlabel = "Power"
    #         if cfg.spec_datas:
    #             cfg.sa.spectrogram.zmin   = cfg.spec_datas['metadata']['y_min']
    #             cfg.sa.spectrogram.zmax   = cfg.spec_datas['metadata']['y_max']
    else:
        # log scale option has been modified
        if '0' in prop_id:
            if log_scale and log_scale[0] == 'on':
                cfg.sa.spectrogram.zlabel =  "Power (dB)"
                cfg.sa.spectrogram.zmin   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_min']+ 1e-12) - 3
                cfg.sa.spectrogram.zmax   = 10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) + 10
                
            else:
                cfg.sa.spectrogram.zlabel = "Power"
                if cfg.spec_datas:
                    cfg.sa.spectrogram.zmin   = float(cfg.spec_datas['metadata']['y_min'])
                    cfg.sa.spectrogram.zmax   = float(cfg.spec_datas['metadata']['y_max'])
        else:
            if log_scale and log_scale[0] == 'on':
                cfg.sa.spec.ylabel = "Power (dB)"
            else:
                cfg.sa.spec.ylabel = "Power" 

    return cfg.sa.spectrogram.get_plot()





if __name__ == '__main__':
    # app.run_server(debug=True, processes=6)
    app.run_server(debug=True)
