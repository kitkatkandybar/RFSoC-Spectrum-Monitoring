import logging
logger = logging.getLogger(__name__)

import dash
import numpy as np

import config as cfg


@dash.callback(
    dash.Output({'type': 'specgram-y-min-input', 'index': dash.MATCH,}, 'value'),
    dash.Input({'type': 'radio-log-scale', 'index': dash.MATCH,}, 'value'),
    dash.State({'type': 'specgram-y-min-input', 'index': dash.MATCH,}, 'value'),
)
def update_spec_ymin_scale(log_scale, y_min):
    if log_scale and log_scale == 'on' and cfg.spec_datas:
            return 10.0 * np.log10(cfg.spec_datas['metadata']['y_min'] + 1e-12) - 3
            
    elif cfg.spec_datas:
        return cfg.spec_datas['metadata']['y_min']


    raise dash.exceptions.PreventUpdate

@dash.callback(
    dash.Output({'type': 'specgram-y-max-input', 'index': dash.MATCH,}, 'value'),
    dash.Input({'type': 'radio-log-scale', 'index': dash.MATCH,}, 'value'),
    dash.State({'type': 'specgram-y-max-input', 'index': dash.MATCH,}, 'value'),
)
def update_spec_ymax_scale(log_scale, y_max):
    if not cfg.spec_datas:
        raise dash.exceptions.PreventUpdate

    if log_scale and log_scale == 'on':
            return 10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) - 3
            
    elif cfg.spec_datas:
        return cfg.spec_datas['metadata']['y_max']

@dash.callback(
    dash.Output({'type': 'spectrum-y-min-input', 'index': dash.MATCH,}, 'value'),
    dash.Input({'type': 'radio-log-scale', 'index': dash.MATCH,}, 'value'),
    dash.State({'type': 'spectrum-y-min-input', 'index': dash.MATCH,}, 'value'),
)
def update_spectrum_ymin_scale(log_scale, y_min):
    if log_scale and log_scale == 'on' and cfg.spec_datas:
            return 10.0 * np.log10(cfg.spec_datas['metadata']['y_min'] + 1e-12) - 3
            
    elif cfg.spec_datas:
        return cfg.spec_datas['metadata']['y_min']


    raise dash.exceptions.PreventUpdate

@dash.callback(
    dash.Output({'type': 'spectrum-y-max-input', 'index': dash.MATCH,}, 'value'),
    dash.Input({'type': 'radio-log-scale', 'index': dash.MATCH,}, 'value'),
    dash.State({'type': 'spectrum-y-max-input', 'index': dash.MATCH,}, 'value'),
)
def update_spectrum_ymax_scale(log_scale, y_min):
    if log_scale and log_scale == 'on' and cfg.spec_datas:
            return 10.0 * np.log10(cfg.spec_datas['metadata']['y_max'] + 1e-12) - 3
            
    elif cfg.spec_datas:
        return cfg.spec_datas['metadata']['y_max']


    raise dash.exceptions.PreventUpdate