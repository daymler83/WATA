"""
Created on Mon Jul 10 15:38:35 2023
@author: DOR
"""

from __future__ import absolute_import, division, print_function

import os
import sys

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go

# Define the path to your Excel file
FILE_PATH = 'C:\Daymler\daymler\Ana_proyecto\WATA_SEGMENTS2.xlsx'

# Function to load data from Excel file
def load_and_process_data(file_path):
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error loading Excel file {file_path}: {e}")
        sys.exit(1)

    df['TOTAL_ON'] = df['TOTAL_ON'].astype(int)
    df = df.sort_values(['FINAL_ETC_ROUTE_NAME', 'TOTAL_ON'], ascending=[True, False])
    df['CUMM_TOTAL'] = df.groupby('FINAL_ETC_ROUTE_NAME')['TOTAL_ON'].cumsum()
    df['%_OF_RIDERS'] = df.groupby('FINAL_ETC_ROUTE_NAME')['CUMM_TOTAL'].apply(lambda x: x / x.iloc[-1])

    return df

# Load and process data
df = load_and_process_data(FILE_PATH)

# Create the Dash app
app = dash.Dash(__name__)

# Define custom styles
styles = {
    'header': {
        'marginBottom': '10px',
        'fontSize': '24px',
        'color': '#555'
    },
    'container': {
        'width': '95%',
        'margin': '0 auto'
    },
    'table': {
        'borderCollapse': 'collapse',
        'width': '100%'
    },
    'tableHeader': {
        'backgroundColor': '#f8f8f8',
        'fontWeight': 'bold',
        'padding': '10px'
    },
    'tableCell': {
        'border': '1px solid #ddd',
        'padding': '10px'
    }
}

# Define the layout of the dashboard
app.layout = html.Div(
    style=styles['container'],
    children=[
        html.Div(
            children=[
                html.H3('Route Map', style=styles['header']),
                dcc.Graph(
                    id='route-map-graph',
                    style={'height': '500px'}
                ),
            ],
            style={'width': '50%', 'display': 'inline-block'}
        ),
        html.Div(
            children=[
                html.H3('Client Segment Map', style=styles['header']),
                dcc.Graph(
                    id='segment-map-graph',
                    style={'height': '500px'}
                ),
            ],
            style={'width': '50%', 'display': 'inline-block'}
        ),
        html.Div(
            id='table-container',
            children=[
                html.H3('Stop Information', style=styles['header']),
                html.Div(
                    id='table-scroll',
                    style={'overflowY': 'scroll', 'maxHeight': '400px'},
                    children=[
                        html.Table(
                            id='table',
                            style=styles['table'],
                            children=[
                                html.Thead(
                                    children=[
                                        html.Tr([
                                            html.Th('Select', style=styles['tableHeader']),
                                            html.Th('Stop', style=styles['tableHeader']),
                                            html.Th('Total Cumm', style=styles['tableHeader']),
                                            html.Th('% Riders', style=styles['tableHeader']),
                                            html.Th('Segment Cliente', style=styles['tableHeader'])
                                        ])
                                    ]
                                ),
                                html.Tbody(id='table-body', children=[])  # Initialize with empty children
                            ]
                        )
                    ]
                )
            ],
            style={'width': '50%', 'margin': '10px'}
        ),
        html.Div(
            id='dropdown-container',
            children=[
                html.Label('Select Route:', style=styles['header']),
                dcc.Dropdown(
                    id='route-dropdown',
                    options=[{'label': route, 'value': route} for route in df['FINAL_ETC_ROUTE_NAME'].unique()],
                    placeholder='Select Route',
                    multi=True,
                    style=styles['tableCell']
                ),
                html.Label('Select Percentage:', style=styles['header']),
                dcc.Dropdown(
                    id='percentage-dropdown',
                    options=[{'label': f'{i}%', 'value': i/100} for i in range(25, 101, 25)],
                    value=1.0,  # Default value to 100%
                    placeholder='Select Percentage',
                    style=styles['tableCell']
                )
            ],
            style={'width': '50%', 'margin': '10px'}
        )
    ]
)

# Callback to update the table based on the selected route and percentage
@app.callback(
    dash.dependencies.Output('table-body', 'children'),
    [dash.dependencies.Input('route-dropdown', 'value'),
     dash.dependencies.Input('percentage-dropdown', 'value')]
)
def update_table(selected_routes, selected_percentage):
    if selected_routes and selected_percentage:
        filtered_df = df[df['FINAL_ETC_ROUTE_NAME'].isin(selected_routes)]

        # Create 'SEGMENT_CLIENTE' based on the selected percentage
        n_segments = int(1 / selected_percentage)
        filtered_df['SEGMENT_CLIENTE'] = pd.qcut(filtered_df['%_OF_RIDERS'], n_segments, labels=False) + 1

        table_rows = []
        for index, row in filtered_df.iterrows():
            table_rows.append(
                html.Tr([
                    html.Td(dcc.Checklist(
                        id={'type': 'stop-checkbox', 'index': index},
                        options=[{'label': '', 'value': 'selected'}],
                        value=[]
                    )),
                    html.Td(row['FINAL_ETC_STOP_NAME'], style=styles['tableCell']),
                    html.Td(row['CUMM_TOTAL'], style=styles['tableCell']),
                    html.Td(row['%_OF_RIDERS'], style=styles['tableCell']),
                    html.Td(row['SEGMENT_CLIENTE'], style=styles['tableCell'])
                ])
            )
        return table_rows
    else:
        return []

# Callback to update the route map based on the selected routes
@app.callback(
    dash.dependencies.Output('route-map-graph', 'figure'),
    [dash.dependencies.Input('route-dropdown', 'value')]
)
def update_maps(selected_routes):
    if selected_routes:
        filtered_df = df[df['FINAL_ETC_ROUTE_NAME'].isin(selected_routes)]

        fig_route = go.Figure()
        for route in selected_routes:
            fig_route.add_trace(go.Scattermapbox(
                lat=filtered_df[filtered_df['FINAL_ETC_ROUTE_NAME'] == route]['stop_lat'],
                lon=filtered_df[filtered_df['FINAL_ETC_ROUTE_NAME'] == route]['stop_lon'],
                mode='markers',
                marker=dict(size=10),
                name=route,
                hoverinfo='text',
                text=filtered_df[filtered_df['FINAL_ETC_ROUTE_NAME'] == route]['FINAL_ETC_STOP_NAME'] +
                     '<br>Total ON: ' +
                     filtered_df[filtered_df['FINAL_ETC_ROUTE_NAME'] == route]['TOTAL_ON'].astype(str),
            ))

        fig_route.update_layout(
            mapbox_style='open-street-map',
            margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
            showlegend=True,
            mapbox=dict(
                center=dict(lat=filtered_df['stop_lat'].mean(), lon=filtered_df['stop_lon'].mean()),
                zoom=10
            )
        )

        return fig_route
    else:
        return {}

# Callback to update the client segment map based on the selected routes and percentage
@app.callback(
    dash.dependencies.Output('segment-map-graph', 'figure'),
    [dash.dependencies.Input('route-dropdown', 'value'),
     dash.dependencies.Input('percentage-dropdown', 'value')]
)
def update_client_segment_map(selected_routes, selected_percentage):
    if selected_routes and selected_percentage:
        # Filter dataframe based on selected routes
        filtered_df = df[df['FINAL_ETC_ROUTE_NAME'].isin(selected_routes)]

        # Calculate client segment based on selected percentage
        n_segments = int(1 / selected_percentage)
        filtered_df['SEGMENT_CLIENTE'] = pd.qcut(filtered_df['%_OF_RIDERS'], n_segments, labels=False) + 1

        fig_segment = go.Figure()
        for route in selected_routes:
            route_data = filtered_df[filtered_df['FINAL_ETC_ROUTE_NAME'] == route]
            for segment in route_data['SEGMENT_CLIENTE'].unique():
                segment_data = route_data[route_data['SEGMENT_CLIENTE'] == segment]
                fig_segment.add_trace(go.Scattermapbox(
                    lat=segment_data['stop_lat'],
                    lon=segment_data['stop_lon'],
                    mode='markers',
                    marker=dict(size=10),
                    name=f"{route} - Segment {segment}",
                    hoverinfo='text',
                    text=segment_data['FINAL_ETC_STOP_NAME'] +
                         '<br>Total ON: ' +
                         segment_data['TOTAL_ON'].astype(str),
                ))

        fig_segment.update_layout(
            mapbox_style='open-street-map',
            margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
            showlegend=True,
            mapbox=dict(
                center=dict(lat=filtered_df['stop_lat'].mean(), lon=filtered_df['stop_lon'].mean()),
                zoom=10
            )
        )

        return fig_segment
    else:
        return {}

from flask import Flask, render_template_string

# Function to generate the HTML code for the dashboard
def generate_dashboard_html(app):
    layout = app.layout
    return render_template_string(str(layout))

# Export function to save the dashboard as an HTML file
def save_dashboard_as_html(app, file_path):
    try:
        dashboard_html = generate_dashboard_html(app)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(dashboard_html)
        print(f"Dashboard successfully saved as HTML: {file_path}")
    except Exception as e:
        print(f"Error saving dashboard as HTML: {e}")

        
# Run the Dash app
if __name__ == '__main__':
    try:
        port = int(sys.argv[1])  # This is for a command-line input
    except:
        port = 8050   # If you don't provide any port, then the port will be set to 8050

    app.run_server(debug=False, port=port, dev_tools_ui=False)

    # Save the dashboard as HTML after running the server
    save_dashboard_as_html(app, 'dashboard.html')