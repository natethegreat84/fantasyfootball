import nfl_data_py as nfl
import pandas as pd
# import os
# import urllib.request
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import dash
from dash import Dash, html, dcc, dash_table, callback, Output, Input
import dash_bootstrap_components as dbc

pbp_rp = nfl.import_seasonal_data([2017,2018,2019,2020,2021,2022])

# pbp_rp = pbp_rp[(pbp_rp['carries'] >= 100) | (pbp_rp['receptions'] >= 40)]

pbp_rp.columns


player_stats = pbp_rp.filter(items=['player_id', 'season', 'games','carries', 'rushing_yards',
       'rushing_tds','receptions', 'targets', 'receiving_yards', 'receiving_tds', 'receiving_yards_after_catch',
       'fantasy_points', 'fantasy_points_ppr'])

player_index = nfl.import_players()
# player_index.columns
player_index = player_index.filter(items=['display_name', 'position', 'gsis_id'])

player_index.rename(columns={'gsis_id':'player_id'}, inplace=True)
# player_index

player_stats = player_stats.merge(player_index, how='left', on='player_id')
player_stats['yards_per_attempt'] = player_stats['rushing_yards'] / player_stats['carries']
player_stats['fp_per_game'] = player_stats['fantasy_points'] / player_stats['games']
player_stats['fp_ppr_per_game'] = player_stats['fantasy_points_ppr'] / player_stats['games']

player_stats = player_stats[player_stats['position'] != 'QB']

player_stats = player_stats.filter(items=['display_name', 'position', 'season', 'games','carries', 'rushing_yards', 'rushing_tds', 'yards_per_attempt',
                                          'receptions', 'targets', 'receiving_yards', 'receiving_tds',
                                          'receiving_yards_after_catch', 'fantasy_points', 'fp_per_game', 'fantasy_points_ppr', 'fp_ppr_per_game'])

player_stats = player_stats.sort_values(['display_name', 'season'])


del player_index
del pbp_rp

dfr = player_stats.melt(id_vars=['season', 'display_name', 'position', 'games'],
                                 var_name='Category',
                                 value_vars=['carries', 'rushing_yards', 'rushing_tds', 'yards_per_attempt',
       'receptions', 'targets', 'receiving_yards', 'receiving_tds',
       'receiving_yards_after_catch', 'fantasy_points', 'fantasy_points_ppr'])
 
app = Dash(__name__)
server = app.server

 
app.layout = dbc.Container([html.H1("Fantasy Football POC"), html.P("Proof of concept to visualize player stats dynamically"),
                    html.H2("Skill Players' Stats - Min 100 carries/40 catches"),
                    html.Div([
                        dcc.Dropdown(
                            dfr['Category'].unique(),
                            'rushing_tds',
                            id='crossfilter-xaxis-column'
                        ), html.P("x-axis category")
                            ],
                            style={'width': '32%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(
                            dfr['Category'].unique(),
                            'carries',
                            id='crossfilter-yaxis-column'
                        ), html.P("y-axis category")
                            ],
                            style={'width': '32%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Dropdown(
                            dfr['Category'].unique(),
                            'fantasy_points',
                            id='crossfilter-zaxis-column'
                        ), html.P("z-axis category")
                            ],
                            style={'width': '32%', 'display': 'inline-block'}),
                    html.Div(dcc.Graph(
                          id='crossfilter-indicator-scatter',
                          hoverData={'points':[{'customdata': 'Derrick Henry'}]}
                            ),
                            style={'width': '49%', 'height':'100%', 'display': 'inline-block', 'padding': '0 20'}),
                    html.Div([dcc.Graph(id='x-time-series'),
                            dcc.Graph(id='y-time-series'),
                            dcc.Graph(id='z-time-series')],
                            style={'display': 'inline-block', 'width': '49%'})
                    ,
                    html.Br(),
                    html.Div([html.P("Season"),
                            dcc.Slider(
                                    dfr['season'].min(),
                                    dfr['season'].max(),
                                    step=1,
                                    id='crossfilter-year-slider',
                                    value=dfr['season'].max(),
                                    marks={str(year): str(year) for year in dfr['season'].unique()}
                                )], style={'width': '49%', 'padding': '0px 20px 20px 20px'}
                            ),
                    html.Br(),
                    html.Div([
                        dcc.Dropdown(
                            player_stats['display_name'].unique(),
                                'Derrick Henry',
                                id='select-player-list'
                                )
                            ],
                            style={'width': '32%', 'display': 'inline-block'}),
                    html.Br(),
                    html.Div(id='diplay-player-stats'),
                    html.Br(),
                    html.Footer("**Github.com - NFLVerse")
                ]
            )
          
 


@callback(
    Output('crossfilter-indicator-scatter', 'figure', allow_duplicate=True),
    Input('crossfilter-xaxis-column', 'value'),
    Input('crossfilter-yaxis-column', 'value'),
    Input('crossfilter-zaxis-column', 'value'),
    Input('crossfilter-year-slider', 'value'),
    prevent_initial_call = True)
def update_graph(xaxis_column_name, yaxis_column_name,zaxis_column_name,
                 year_value):
    
    dff = dfr[dfr['season'] == year_value] 
 
    fig = px.scatter_3d(x=dff[dff['Category'] == xaxis_column_name]['value'],
            y=dff[dff['Category'] == yaxis_column_name]['value'],
            z=dff[dff['Category'] == zaxis_column_name]['value'],
            hover_name=dff[dff['Category'] == yaxis_column_name]['display_name']
            )
    
    fig.update_scenes(xaxis_title=xaxis_column_name,
                      yaxis_title=yaxis_column_name,
                      zaxis_title=zaxis_column_name) 
    
    fig.update_traces(customdata=dff[dff['Category'] == yaxis_column_name]['display_name'], marker_size=5)

 
    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest', showlegend=False)
    fig.update_layout(showlegend = False)
 
    return fig
 
 
def create_time_series(dff, title):
 
    fig = px.scatter(dff, x='season', y='value')
 
    fig.update_traces(mode='lines+markers')
 
    fig.update_xaxes(showgrid=False)
 
    fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
                       xref='paper', yref='paper', showarrow=False, align='left',
                       text=title)
 
    fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})
 
    return fig
 
 
@callback(
    Output('x-time-series', 'figure', allow_duplicate=True),
    Input('crossfilter-indicator-scatter', 'hoverData'),
    Input('crossfilter-xaxis-column', 'value'),
    prevent_initial_call=True)
def update_x_timeseries_from_plot(hoverData, xaxis_column_name):
    player_name = hoverData['points'][0]['customdata']
    dff = dfr[dfr['display_name'] == player_name]
    dff = dff[dff['Category'] == xaxis_column_name]
    title = '<b>{}</b><br>{}'.format(player_name, xaxis_column_name)
    return create_time_series(dff, title)

 
@callback(
    Output('y-time-series', 'figure', allow_duplicate=True),
    Input('crossfilter-indicator-scatter', 'hoverData'),
    Input('crossfilter-yaxis-column', 'value'),
    prevent_initial_call=True)
def update_y_timeseries_from_plot(hoverData, yaxis_column_name):
    dff = dfr[dfr['display_name'] == hoverData['points'][0]['customdata']]
    dff = dff[dff['Category'] == yaxis_column_name]
    return create_time_series(dff, yaxis_column_name)

@callback(
    Output('z-time-series', 'figure', allow_duplicate=True),
    Input('crossfilter-indicator-scatter', 'hoverData'),
    Input('crossfilter-zaxis-column', 'value'),
    prevent_initial_call=True)
def update_z_timeseries_from_plot(hoverData, zaxis_column_name):
    dff = dfr[dfr['display_name'] == hoverData['points'][0]['customdata']]
    dff = dff[dff['Category'] == zaxis_column_name]
    return create_time_series(dff, zaxis_column_name)

@callback(
    Output('diplay-player-stats', 'children', allow_duplicate=True),
    Output('select-player-list', 'value', allow_duplicate=True),
    Input('crossfilter-indicator-scatter', 'hoverData'),
    prevent_initial_call = True
 )
def show_player_stats_from_plot(hoverData):
    player_name = hoverData['points'][0]['customdata']
    dfs = player_stats[player_stats['display_name'] == player_name]

    dfs = dfs.sort_values('season')

    return dash_table.DataTable(data=dfs.to_dict('records'),
                columns=[{'id': c, 'name': c} for c in dfs.columns]), player_name
                
@callback(
    Output('diplay-player-stats', 'children'),
    Input('select-player-list', 'value')
 )
def show_player_stats(player_name):
    df = player_stats[player_stats['display_name'] == player_name]

    df = df.sort_values('season')

    return dash_table.DataTable(data=df.to_dict('records'),
                columns=[{'id': c, 'name': c} for c in df.columns])

@callback(
    Output('x-time-series', 'figure'),
    Input('select-player-list', 'value'),
    Input('crossfilter-xaxis-column', 'value'))
def update_x_timeseries(hoverData, xaxis_column_name):
    player_name = hoverData
    dff = dfr[dfr['display_name'] == player_name]
    dff = dff[dff['Category'] == xaxis_column_name]
    title = '<b>{}</b><br>{}'.format(player_name, xaxis_column_name)
    return create_time_series(dff, title)

 
@callback(
    Output('y-time-series', 'figure'),
    Input('select-player-list', 'value'),
    Input('crossfilter-yaxis-column', 'value'))
def update_y_timeseries(hoverData, yaxis_column_name):
    dff = dfr[dfr['display_name'] == hoverData]
    dff = dff[dff['Category'] == yaxis_column_name]
    return create_time_series(dff, yaxis_column_name)

@callback(
    Output('z-time-series', 'figure'),
    Input('select-player-list', 'value'),
    Input('crossfilter-zaxis-column', 'value'))
def update_z_timeseries(hoverData, zaxis_column_name):
    dff = dfr[dfr['display_name'] == hoverData]
    dff = dff[dff['Category'] == zaxis_column_name]
    return create_time_series(dff, zaxis_column_name)

@callback(
    Output('crossfilter-indicator-scatter', 'figure'),
    Input('crossfilter-xaxis-column', 'value'),
    Input('crossfilter-yaxis-column', 'value'),
    Input('crossfilter-zaxis-column', 'value'),
    Input('crossfilter-year-slider', 'value'),
    Input('select-player-list', 'value'))
def update_graph_from_dropdown(xaxis_column_name, yaxis_column_name,zaxis_column_name,
                 year_value, hoverData):
    
    dff = dfr[dfr['season'] == year_value] 

    dff['hover'] = np.where(dff['display_name']==hoverData,"yes","no")
 
    fig = px.scatter_3d(x=dff[dff['Category'] == xaxis_column_name]['value'],
            y=dff[dff['Category'] == yaxis_column_name]['value'],
            z=dff[dff['Category'] == zaxis_column_name]['value'],
            hover_name=dff[dff['Category'] == yaxis_column_name]['display_name'],
            color = dff[dff['Category'] == yaxis_column_name]['hover']
            )
    
    fig.update_scenes(xaxis_title=xaxis_column_name,
                      yaxis_title=yaxis_column_name,
                      zaxis_title=zaxis_column_name) 
    
    fig.update_traces(customdata=dff[dff['Category'] == yaxis_column_name]['display_name'], marker_size=5)

 
    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest', showlegend=False)
    fig.update_layout(showlegend = False)

    return fig
 
 
if __name__ == '__main__':
    app.run(debug=True)
