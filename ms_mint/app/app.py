
import os

import tempfile

import pandas as pd

from pathlib import Path as P

import matplotlib
matplotlib.use('Agg')

import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc

import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_extensions import Download
from dash_extensions.enrich import FileSystemCache

from flask_caching import Cache
from flask_login import current_user


from . import tools as T

from . import workspaces
from . import ms_files
from . import metadata
from . import targets
from . import peak_optimization
from . import processing
from . import add_metab
from . import analysis
from . import messages

import dash_uploader as du
from tempfile import gettempdir


def make_dirs():
    tmpdir = tempfile.gettempdir()
    tmpdir = os.path.join(tmpdir, 'MINT')
    tmpdir = os.getenv('MINT_DATA_DIR', default=tmpdir)
    cachedir = os.path.join(tmpdir, '.cache')
    os.makedirs(tmpdir, exist_ok=True)
    os.makedirs(cachedir, exist_ok=True)
    return tmpdir, cachedir

TMPDIR, CACHEDIR = make_dirs()

fsc = FileSystemCache(CACHEDIR)

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "simple", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}

pd.options.display.max_colwidth = 1000

_modules = [
  workspaces,
  ms_files,
  metadata,
  targets,
  add_metab,
  peak_optimization,
  processing,
  analysis
]

modules = {module._label: module for module in _modules}

# Collect outputs:
_outputs = html.Div(id='outputs', children=[module._outputs for module in 
                                     _modules if module._outputs is not None], 
             style={'visibility': 'hidden'})

app = dash.Dash(__name__, 
    external_stylesheets=[
        dbc.themes.MINTY,
        "https://codepen.io/chriddyp/pen/bWLwgP.css"
        ],
    requests_pathname_prefix=os.getenv('MINT_SERVE_PATH', default='/'),
    routes_pathname_prefix=os.getenv('MINT_SERVE_PATH', default='/')
    )

app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

UPLOAD_FOLDER_ROOT = gettempdir()
du.configure_upload(app, UPLOAD_FOLDER_ROOT)


cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': '/tmp/MINT-cache'
})

app.title = 'MINT'

app.config['suppress_callback_exceptions'] = True


logout_button = dbc.Button("Logout", id="logout-button", style={'marginRight': '10px'}),
logout_button = html.A(href='/logout', children=logout_button)

app.layout = html.Div([
    #html.Img(src=app.get_asset_url('logo.png'), style={'height': '30px'}),

    html.Div(logout_button),

    dcc.Interval(id="progress-interval", n_intervals=0, interval=500, disabled=False),

    html.A(href='https://sorenwacker.github.io/ms-mint/gui/', 
         children=[html.Button('Documentation', id='B_help', style={'float': 'right', 'color': 'info'})],
         target="_blank"),

    html.A(href=f'https://github.com/sorenwacker/ms-mint/issues/new?body={T.get_issue_text()}', 
         children=[html.Button('Issues', id='B_issues', style={'float': 'right', 'color': 'info'})],
         target="_blank"),

    dbc.Progress(id="progress-bar", value=100, style={'marginBottom': '20px', 'width': '100%', 'marginTop': '20px'}),

    messages.layout(),

    Download(id='res-download-data'),

    html.Div(id='tmpdir', children=TMPDIR, style={'visibility': 'hidden'}),

    html.P('Current Workspace: ', style={'display': 'inline-block', 'marginRight': '5px', 'marginTop': '5px'}),

    html.Div(id='active-workspace', style={'display': 'inline-block'}),

    html.Div(id='wdir', children='', style={'display': 'inline-block', 'visibility': 'visible', 'float': 'right'}),

    html.Div(id='pko-creating-chromatograms'),

    dcc.Tabs(id='tab', value=_modules[0]._label,
        children=[
            dcc.Tab(id=modules[key]._label,
                    value=key, 
                    label=modules[key]._label,
                    )
            for key in modules.keys()]
    ),

    html.Div(id='pko-image-store', style={'visibility': 'hidden', 'height': '0px'}),

    html.Div(id='tab-content'),

    _outputs
    
], style={'margin':'2%'})


def register_callbacks(app):
        
    messages.callbacks(app=app, fsc=fsc, cache=cache)

    for module in _modules:
        func = module.callbacks
        if func is not None:
            print('Register callbacks for', module)
            func(app=app, fsc=fsc, cache=cache)


    @app.callback(
        Output('tab-content', 'children'),
        Input('tab', 'value'),
        State('wdir', 'children')
    )
    def render_content(tab, wdir):
        func = modules[tab].layout
        if tab != 'Workspaces' and wdir == '':
            return dbc.Alert('Please, create and activate a workspace.', color='warning')
        elif tab in ['Metadata', 'Peak Optimization', 'Processing'] and len(T.get_ms_fns( wdir )) == 0:
            return dbc.Alert('Please import MS files.', color='warning')
        elif tab in ['Processing'] and ( len(T.get_targets( wdir )) == 0 ):
            return dbc.Alert('Please, define targets.', color='warning')
        elif tab in ['Analysis'] and not P(T.get_results_fn( wdir )).is_file():
            return dbc.Alert('Please, create results (Processing).', color='warning')
        if func is not None:
            return func()
        else:
            raise PreventUpdate

    @app.callback(
        Output('tmpdir', 'children'),
        Output('logout-button', 'style__visibility'),
        Input('progress-interval', 'value')
    )
    def upate_tmpdir(x):
        if current_user is not None:
            username = current_user.username
            print('User:', username)
            return str(P(TMPDIR)/username), 'visible'
        return str(TMPDIR), 'hidden'


if __name__ == '__main__':
    register_callbacks(app)
    app.run_server(debug=True, threaded=True, 
        dev_tools_hot_reload_interval=5000,
        dev_tools_hot_reload_max_retry=30)
