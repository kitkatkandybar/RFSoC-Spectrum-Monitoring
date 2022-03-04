import dash
from dash import dcc
from dash import html



stream_sidebar_components = html.Div([
	html.Div(id='stream-picker-div', style={'width': '100%'},
		children = [
	        html.H4("Choose the stream:"),
	        dcc.Dropdown(
	            id={
	                'type': 'stream-picker', 'index': 0, 

	            }
	        ),
	    ]
	),
	html.Div(id='stream-metadata-div', style={'width': '100%'}),
	html.Div(id='play-stream-div', style={'width': '100%'}),
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
                    'type': 'radio-log-scale', 'index': 1, 
                },
                labelStyle={"verticalAlign": "middle"},
                className="plot-display-radio-items",
            )
        ],
        className="radio-item-div",
    ),

])