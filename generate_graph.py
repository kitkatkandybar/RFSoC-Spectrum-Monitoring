import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import numpy as np

from spectrum_analyzer import SpectrumAnalyzer
from digital_rf_utils import read_digital_rf_data


def generate_spectrum_analyzer_figure(id, fig, sample_min = 0, sample_max = 1000000, sample_step = 10000, sample_start_default = 300000, sample_stop_default = 700000 ):
    return html.Div(children = [
        dcc.Graph(
            id = id,
            figure = fig
        ),
        html.H4(children='enter file path:'),
        dcc.Input(placeholder='enter text', type='text'),
        html.H4(children=' '),
        dcc.RadioItems(
            options=[
                {'label': 'Log Scale', 'value': 'log_scale'},
                {'label': 'Linear Scale', 'value': 'linear_scale'}
            ],
            value= 'linear_scale'
        ),
        html.H4(children='antenna type:'),
        dcc.Dropdown(
            options=[
                {'label': 'discone', 'value': 'discone'},
                {'label': 'lwa_ew', 'value': 'lwa_ew'},
                {'label': 'lwa_ns', 'value': 'lwa_ns'},
                {'label': 'monopole', 'value': 'monopole'}
            ],
            value=''
        ),
        html.H4(children='sample range:'),
        dcc.RangeSlider(
            id = id + "_range_slider",
            min=sample_min,
            max=sample_max,
            step=sample_step,
            value=[sample_start_default, sample_stop_default]
        ),
        html.Div(id= id + '-output-container-range-slider'),
        html.H4(children='number of bins:'),
        dcc.Slider(
            min = 8,
            max = 10,
            step = None,
            marks= {i: '{}'.format(2 ** i) for i in range(8, 11)}
        )
    ])

fig1 = dict(
            data=[
                dict(
                    x=[1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
                    2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012],
                    y=[219, 146, 112, 127, 124, 180, 236, 207, 236, 263,
                    350, 430, 474, 526, 488, 537, 500, 439],
                    name='Rest of world',
                    marker=dict(
                        color='rgb(55, 83, 109)'
                    )
                ),
                dict(
                    x=[1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003,
                    2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012],
                    y=[16, 13, 10, 11, 28, 37, 43, 55, 56, 88, 105, 156, 270,
                    299, 340, 403, 549, 499],
                    name='China',
                    marker=dict(
                        color='rgb(26, 118, 255)'
                    )
                )
            ],
            layout=dict(
                title='US Export of Plastic Scrap',
                showlegend=True,
                legend=dict(
                    x=0,
                    y=1.0
                ),
                margin=dict(l=40, r=0, t=40, b=30)
            )
        )

app = dash.Dash(__name__)

id = "test_id"
app.layout = html.Div([
    html.H4(children='generate_spectrum_analyzer_figure'),
    generate_spectrum_analyzer_figure(id, fig1)
])

@app.callback(
    dash.dependencies.Output(id +'-output-container-range-slider', 'children'),
    [dash.dependencies.Input(id + '_range_slider', 'value')])
def update_output(value):
    return 'You have selected "{}"'.format(value)



if __name__ == '__main__':
    app.run_server(debug=True)

