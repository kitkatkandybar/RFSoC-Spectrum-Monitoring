import dash
import pytz
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_html_components as html
import plotly.graph_objects as go  # p
from datetime import datetime, timedelta
import numpy as np
import redis
import pandas as pd
import json


def generate_app(config, config_yaml_path=None, debug=False):

    streamname = "example"
    external_stylesheets = [dbc.themes.BOOTSTRAP]
    # Redis set up
    redis_config = dict(host="localhost", port=6379, db="0")
    redis_host = redis_config["host"]
    redis_port = redis_config["port"]
    redis_password = ""

    # Get redis client
    r_clt = redis.Redis(host="localhost", port=6379, db=0)

    # dash app set up
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
    # Create the graph place and the update timer
    intup = 10 * 1000
    n_ints = 0
    cur_div = html.Div(
        [
            dcc.Graph(id="data", style={"display": "inline-block"}),
            dcc.Interval(id="dataupdate", interval=intup, n_intervals=n_ints),
        ],
        className="four columns",
    )
    r_0 = [cur_div]
    r_0 = html.Div(children=r_0, className="row")
    # add the storage terms
    st_list = [dcc.Store(id="x_accume"), dcc.Store(id="x")]
    app.layout = html.Div(st_list + [r_0])

    # Call backs with decorators
    @app.callback(
        [Output("x_accume", "data"), Output("x", "data")],
        [Input("dataupdate", "n_intervals")],
        Input("x_accume", "data"),
    )
    def updatedata(n, x_accumejson):
        """Update the storage.

        Parameters
        ----------
        n : int
            Number of callbacks
        x_accumejson : str
            JSON string of the accumulated data.

        Returns
        -------
        x_accumejson : str
            JSON string of the accumulated data.
        xjson :
            JSON string of the accumulated data.
        """

        rstrm = r_clt.xread({streamname: "$"}, None, 0)

        xlist = json.loads(rstrm[0][1][0][1][b"data"])
        xnew = np.array(xlist)
        if x_accumejson is None:
            x_accume = 0.0
        else:
            x_accume = np.array(json.loads(x_accumejson))

        x_accume += xnew
        x = xnew
        return json.dumps(x_accume.tolist()), json.dumps(x.tolist())

    @app.callback(
        [
            Output("data", "figure"),
        ],
        [
            Input("dataupdate", "n_intervals"),
            Input("x_accume", "data"),
            Input("x", "data"),
        ],
    )
    def updateplot(n, x_accumejson, xjson):
        """Update the plot.

        Update the plot with the count.

        Parameters
        ---------
        n : int
            Number of callbacks
        x_accumejson : str
            JSON string of the accumulated data.
        xjson :
            JSON string of the accumulated data.

        Returns
        -------
        outlist : list
            List of figures fo the app.
        """

        curfig = go.Figure()

        # Get the current state of the data and make histograms
        x_accume = np.array(json.loads(x_accumejson))
        x = np.array(json.loads(xjson))
        HIST_BINS = np.linspace(-2, 2, 200)
        if n == 0:
            ndiv = 1
        else:
            ndiv = n

        nhist, _ = np.histogram(x_accume / ndiv, HIST_BINS, density=True)
        nsingle, _ = np.histogram(x, HIST_BINS, density=True)
        # Add the traces to the plotss
        curfig.add_trace(
            go.Scatter(
                x=HIST_BINS[:-1],
                y=nhist / nhist.max(),  # upper threshold
                mode="lines",
                name="Accumated histogram",
                marker=dict(color="blue"),
            )
        )
        curfig.add_trace(
            go.Scatter(
                x=HIST_BINS[:-1],
                y=nsingle / nsingle.max(),  # upper threshold
                mode="lines",
                name="Current Data",
                marker=dict(color="red"),
            )
        )
        curfig.update_layout(
            title="Histogram count {0}".format(n),
            xaxis_title="x",
            yaxis_title="Count(normalized)",
        )
        curfig.update_xaxes(showgrid=True, zeroline=False, showline=True)
        curfig.update_yaxes(showgrid=True, zeroline=False, showline=True)

        return [curfig]

    return app


if __name__ == "__main__":
    app = generate_app(None, True)
    app.run_server(debug=True)
