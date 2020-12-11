import dash_html_components as html
import dash_core_components as dcc
from dash_table import DataTable


ws_table = html.Div(id='ws-table-container', 
    style={'min-height':  100, 'margin': '5%'},
    children=[
        DataTable(id='ws-table',
            columns=[ {"name": i, "id": i, "selectable": True}  
                                for i in ['Workspace']],
                    data=[],
                    row_selectable='multi',
                    row_deletable=False,
                    style_cell={'textAlign': 'left'},
                    sort_action='native'
                    )
])


ws_layout = html.Div([
    html.H3('Workspaces'),
    dcc.Input(id='ws-name', placeholder='New workspace name'),
    html.Button('Create Workspace', id='ws-create'),
    html.P(id='ws-create-output'),
    ws_table
])

