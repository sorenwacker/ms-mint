#!/usr/env python

import io
import sys

import colorlover as cl
import numpy as np
import pandas as pd
import uuid

from datetime import date, datetime
from flask import send_file
from functools import lru_cache
from glob import glob
from plotly.subplots import make_subplots
from tkinter import Tk, filedialog

from os.path import basename, isfile, abspath, join

import dash
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_table import DataTable

import plotly.graph_objects as go
import plotly.figure_factory as ff
import plotly.express as px

from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import pdist, squareform

from ms_mint.Mint import Mint
from ms_mint.tools import STANDARD_PEAKFILE
from ms_mint.Layout import Layout
from ms_mint.button_style import button_style

mint = Mint()
mint.peaklist = STANDARD_PEAKFILE

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, "https://codepen.io/chriddyp/pen/bWLwgP.css"])
app.title = 'MINT'
app.layout = Layout


@app.callback(
    [Output("progress-bar", "value"), 
     Output("progress", 'children')],
    [Input("progress-interval", "n_intervals")])
def update_progress(n):
    progress = mint.progress
    # only add text after 5% progress to ensure text isn't squashed too much
    return progress, (f"Progress: {progress} %" if progress >= 5 else "")

### Load MS-files
@app.callback(
    Output('B_add-files', 'value'),
    [Input('B_add-files', 'n_clicks')],
    [State('files-check', 'value')] )
def select_files(n_clicks, options):
    if n_clicks is not None:
        root = Tk()
        root.withdraw()
        root.call('wm', 'attributes', '.', '-topmost', True)
        if 'by-dir' not in options:
            files = filedialog.askopenfilename(multiple=True)
            files = [abspath(i) for i in files]
            for i in files:
                assert isfile(i)
        else:
            dir_ = filedialog.askdirectory()
            if isinstance(dir_ , tuple):
                dir_ = []
            if len(dir_) != 0:
                files = glob(join(dir_, join('**', '*.mzXML')), recursive=True)
            else:
                files = []
        if len(files) != 0:
            mint.files += files
        root.destroy()
    return str(n_clicks)

### Clear files
@app.callback(
    Output('B_files-clear', 'value'),
    [Input('B_files-clear', 'n_clicks')])
def clear_files(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    mint.files = []
    return str(n_clicks)
    
### Update n-files text when files added or cleared
@app.callback(
    [Output('files-text', 'children'),
     Output('n_files_selected', 'children')],
    [Input('B_add-files', 'value'),
    Input('B_files-clear', 'value')])    
def update_files_text(n,k):
        return '{} data files selected.'.format(mint.n_files), mint.n_files


### Load peaklist files
@app.callback(
    [Output('peaklist-text', 'children'),
     Output('n_peaklist_selected', 'children')],
    [Input('B_select-peaklists', 'n_clicks')] )
def select_peaklist(n_clicks):
    if n_clicks is not None:
        root = Tk()
        root.withdraw()
        root.call('wm', 'attributes', '.', '-topmost', True)
        files = filedialog.askopenfilename(multiple=True)
        files = [i  for i in files if i.endswith('.csv')]
        if len(files) != 0:
            mint.peaklist_files = files
        root.destroy()
    return '{} peaklist-files selected.'.format(mint.n_peaklist_files), mint.n_peaklist_files

@app.callback(
    [Output('B_select-peaklists', 'style'),
     Output('B_add-files', 'style'),
     Output('run', 'style')],
    [Input('n_peaklist_selected', 'children'),
     Input('n_files_selected', 'children')])
def run_button_style(n_peaklists, n_files):
    if n_peaklists == 0:
        style_peaklists = button_style('next')
        style_files = button_style()
        style_run = button_style('wait')
    elif n_files == 0:
        style_peaklists = button_style('ready')
        style_files= button_style('next')
        style_run = button_style('wait')
    else:
        style_peaklists = button_style('ready')
        style_files = button_style('ready')
        style_run = button_style('next')
    return style_peaklists, style_files, style_run

@app.callback(
    Output('cpu-text', 'children'),
    [Input('n_cpus', 'value')] )
def mint_cpu_info(value):
    return f'Using {value} cores.'

@app.callback(
    Output('storage', 'children'),
    [Input('run', 'n_clicks')],
    [State('n_cpus', 'value')])
def run_mint(n_clicks, n_cpus):
    if n_clicks is not None:
        mint.run(nthreads=n_cpus)
    return mint.results.to_json(orient='split')


### Data Table
@app.callback(
    [Output('run-out', 'children'),
     Output('peak-select', 'options')],
    [Input('storage', 'children'),
     Input('label-regex', 'value'),
     Input('table-value-select', 'value')])
def get_table(json, label_regex, col_value):
    df = pd.read_json(json, orient='split')
    if len(df) == 0:
        raise PreventUpdate
    
    if df['msFile'].apply(basename).value_counts().max() > 1:
        df['msFile'] = df['msFile'].apply(basename)
        
    try:
        # Generate label without file extention
        labels = [ '.'.join(i.split('.')[:-1]).split('_')[int(label_regex)] for i in df.msFile ]
        df['Label'] = labels
    except:
        df['Label'] = df.msFile
    
    cols = ['Label', 'peakLabel',
            'peakArea', 'rt_max_intensity', 'intensity_median',
            'intensity_max', 'intensity_min', 'msPath', 'msFile', 'fileSize[MB]',
            'intensity sum', 'peakListFile', 'peakMz', 'peakMzWidth[ppm]',
            'rtmin', 'rtmax'] 
               
    df = df[cols]
    biomarker_names = df.peakLabel.drop_duplicates().sort_values().values

    if col_value in ['peakArea', 'rt_max_intensity']:
        df = pd.crosstab(df.peakLabel, df.Label, df[col_value], aggfunc=np.mean).astype(np.float64).T
        if col_value in ['peakArea']:
               df = df.round(0)
        df.reset_index(inplace=True)
        df.fillna(0, inplace=True)
    
    df.columns = df.columns.astype(str)
        
    table = DataTable(
                id='table',
                columns=[{"name": i, "id": i, "selectable": True} for i in df.columns],
                data=df.to_dict('records'),
                sort_action="native",
                sort_mode="single",
                row_selectable="multi",
                selected_rows=[],
                page_action="native",
                page_current= 0,
                page_size= 30,
                style_table={'overflowX': 'scroll'},
                style_as_list_view=True,
                style_cell={'padding': '5px'},
                style_header={'backgroundColor': 'white',
                            'fontWeight': 'bold'},
            )
    return table, [ {'label': i, 'value': i} for i in biomarker_names]

@app.callback(
    Output('heatmap', 'figure'),
    [Input('B_peakAreas', 'n_clicks'),
     Input('checklist', 'value')],
    [State('table', 'derived_virtual_indices'),
     State('table', 'data'),
     State('table-value-select', 'value')])
def plot_0(n_clicks, options, ndxs, data, column):
    if (n_clicks is None) or (column == 'full') or (len(data) == 0):
        raise PreventUpdate
    
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    df = pd.DataFrame(data).set_index('Label').select_dtypes(include=numerics)
       
    plot_type = 'Heatmap'
    colorscale = 'Blues'
    plot_attributes = []
    
    if 'normed' in options:
        df = df.divide(df.max()).fillna(0)
        plot_attributes.append('normalized')

    if 'transposed' in options:
        df = df.T
        
    if 'corr' in options:
        plot_type = 'Correlation'
        df = df.corr()
        colorscale = [[0.0, "rgb(165,0,38)"],
                [0.1111111111111111, "rgb(215,48,39)"],
                [0.2222222222222222, "rgb(244,109,67)"],
                [0.3333333333333333, "rgb(253,174,97)"],
                [0.4444444444444444, "rgb(254,224,144)"],
                [0.5555555555555556, "rgb(224,243,248)"],
                [0.6666666666666666, "rgb(171,217,233)"],
                [0.7777777777777778, "rgb(116,173,209)"],
                [0.8888888888888888, "rgb(69,117,180)"],
                [1.0, "rgb(49,54,149)"]]
    else:
        plot_type = 'Heatmap'
        
    if 'clustered' in options:
        D = squareform(pdist(df, metric='seuclidean'))
        Y = linkage(D, method='complete')
        Z = dendrogram(Y, orientation='left', no_plot=True)['leaves']
        Z.reverse()
        df = df.iloc[Z,:]
        if 'corr' in options:
            df = df[df.index]
            
        dendro_side = ff.create_dendrogram(df, orientation='right', labels=df.index)

    heatmap = go.Heatmap(z=df.values,
                         x=df.columns,
                         y=df.index,
                         colorscale = colorscale)
    
    title = f'{plot_type} of {",".join(plot_attributes)} {column}'

    # Figure without side-dendrogram
    if (not 'dendrogram' in options) or (not 'clustered' in options):
        fig = go.Figure(heatmap)
        fig.update_layout(
            title={'text': title,  },
            yaxis={'title': '', 
                   'tickmode': 'array', 
                   'automargin': True}) 
        fig.update_layout({'height':800, 
                           'hovermode': 'closest'})
        
    else:  # Figure with side-dendrogram
        fig = go.Figure()
        
        for i in range(len(dendro_side['data'])):
            dendro_side['data'][i]['xaxis'] = 'x2'

        for data in dendro_side['data']:
            fig.add_trace(data)
            
        y_labels = heatmap['y']
        heatmap['y'] = dendro_side['layout']['yaxis']['tickvals']
        
        fig.add_trace(heatmap)     

        fig.update_layout(
                {'height':800,
                 'showlegend':False,
                 'hovermode': 'closest',
                 'paper_bgcolor': 'white',
                 'plot_bgcolor': 'white'
                },
                title={'text': title},
                
                # X-axis of main figure
                xaxis={'domain': [.11, 1],        
                       'mirror': False,
                       'showgrid': False,
                       'showline': False,
                       'zeroline': False,
                       'showticklabels': True,
                       'ticks':""
                      },
                # X-axis of side-dendrogram
                xaxis2={'domain': [0, .1],  
                        'mirror': False,
                        'showgrid': True,
                        'showline': False,
                        'zeroline': False,
                        'showticklabels': False,
                        'ticks':""
                       },
                # Y-axis of main figure
                yaxis={'domain': [0, 1],
                       'mirror': False,
                       'showgrid': False,
                       'showline': False,
                       'zeroline': False,
                       'showticklabels': False,
                      })
        fig['layout']['yaxis']['ticktext'] = np.asarray(y_labels)
        fig['layout']['yaxis']['tickvals'] = np.asarray(dendro_side['layout']['yaxis']['tickvals'])
    return fig


@lru_cache(maxsize=32)
@app.callback(
    Output('peakShape', 'figure'),
    [Input('B_peakShapes', 'n_clicks')],
    [State('n_cols', 'value'),
     State('check_peakShapes', 'value')])
def plot_1(n_clicks, n_cols, options):
    if (n_clicks is None) or (mint.rt_projections is None):
        raise PreventUpdate
    files = mint.crosstab.columns
    labels = mint.crosstab.index
    fig = make_subplots(rows=len(labels)//n_cols+1, 
                        cols=n_cols, 
                            subplot_titles=labels)
    
    if len(files) < 13:
        # largest color set in colorlover is 12
        colors = cl.scales['12']['qual']['Paired']
    else:
        colors = cl.interp( cl.scales['12']['qual']['Paired'], len(files))
            
    for label_i, label in enumerate(labels):
        for file_i, file in enumerate(files):

            data = mint.rt_projections[label][file]
            ndx_r = (label_i // n_cols)+1
            ndx_c = label_i % n_cols + 1
            
            fig.add_trace(
                go.Scatter(x=data.index, 
                        y=data.values,
                        name=basename(file),
                        mode='lines',
                        legendgroup=file_i,
                        showlegend=(label_i == 0),  
                        marker_color=colors[file_i],
                        text=file),
                row=ndx_r,
                col=ndx_c,
            )
            
            fig.update_xaxes(title_text="Retention Time", row=ndx_r, col=ndx_c)
            fig.update_yaxes(title_text="Intensity", row=ndx_r, col=ndx_c)

    fig.update_layout(height=200*len(labels), title_text="Peak Shapes")
    fig.update_layout(xaxis={'title': 'test'})
    
    if 'legend_horizontal' in options:
        fig.update_layout(legend_orientation="h")

    if 'legend' in options:
        fig.update_layout(showlegend=True)
    return fig


@lru_cache(maxsize=32)
@app.callback(
    Output('peakShape3d', 'figure'),
    [Input('B_peakShapes3d', 'n_clicks'),
    Input('peak-select', 'value'),
    Input('check_peakShapes3d', 'value')])
def plot_3d(n_clicks, peakLabel, options):
    if (n_clicks is None) or (mint.rt_projections is None) or (peakLabel is None):
        raise PreventUpdate
    data = mint.rt_projections[peakLabel]
    samples = []
    for i, key in enumerate(list(data.keys())):
        sample = data[key].to_frame().reset_index()
        sample.columns = ['retentionTime', 'intensity']
        sample['peakArea'] = sample.intensity.sum()
        sample['msFile'] = basename(key)
        samples.append(sample)
    samples = pd.concat(samples)
    fig = px.line_3d(samples, x='retentionTime', y='peakArea' , z='intensity', color='msFile')
    fig.update_layout({'height': 800})
    if 'legend_horizontal' in options:
        fig.update_layout(legend_orientation="h")

    if not 'legend' in options:
        fig.update_layout(showlegend=False)
    fig.update_layout({'title': peakLabel})
    return fig


## Results Export (Download)
@app.server.route('/export/')
def download_csv():
    file_buffer = io.BytesIO()
    
    writer = pd.ExcelWriter(file_buffer) #, engine='xlsxwriter')
    mint.results.to_excel(writer, 'Results Complete', index=False)
    mint.crosstab.T.to_excel(writer, 'PeakArea Summary', index=True)
    meta = pd.DataFrame({'Version': [mint.version], 
                            'Date': [str(date.today())]}).T[0]
    meta.to_excel(writer, 'MetaData', index=True, header=False)
    writer.close()
    
    file_buffer.seek(0)
    
    now = datetime.now().strftime("%Y-%m-%d")
    uid = str(uuid.uuid4()).split('-')[-1]
    return send_file(file_buffer,
                     attachment_filename=f'MINT__results_{now}-{uid}.xlsx',
                     as_attachment=True,
                     cache_timeout=0)


if __name__ == '__main__':
    
    args = sys.argv
    
    if '--debug' in args:
        DEBUG = True
        mint.files = glob('/data/metabolomics_storage/MINT_demo_files/**/*.mzXML', recursive=True)
    else:
        DEBUG = False

    if '--data' in args:
        if isfile('/tmp/mint_results.csv'):
            mint._results = pd.read_csv('/tmp/mint_results.csv')
        for i in mint.files:
            assert isfile(i)
        for i in mint.peaklist_files:
            assert isfile(i)
    
    app.run_server(debug=DEBUG, port=9999)
