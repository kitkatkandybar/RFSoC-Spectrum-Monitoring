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
	

])