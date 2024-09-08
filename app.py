# Import necessary libraries
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff

# Initialize the Dash app
app = Dash(__name__)

# Load datasets
vehicle_registration_df = pd.read_csv('Whole_Fleet_Vehicle_Registration_Snapshot_by_Postcode_Q2_2024.csv', low_memory=False)
public_transport_df = pd.read_csv('Annual_Metropolitan_Train_Station_Entries_2023-24.csv', low_memory=False)
bicycle_network_df = pd.read_csv('Principal_Bicycle_Network_(PBN).csv', low_memory=False)

# Clean datasets by filling missing values
vehicle_registration_df.fillna(0, inplace=True)
public_transport_df.fillna(0, inplace=True)
bicycle_network_df.fillna(0, inplace=True)

# Filter numeric columns
vehicle_registration_numeric = vehicle_registration_df.select_dtypes(include=['float64', 'int64'])
public_transport_numeric = public_transport_df.select_dtypes(include=['float64', 'int64'])
bicycle_network_numeric = bicycle_network_df.select_dtypes(include=['float64', 'int64'])

# Dash layout with graphs and correlation heatmap
app.layout = html.Div([
    html.H1("Urban Transportation Insights Dashboard"),

    # Dataset dropdown for correlation heatmap
    html.Label("Select Dataset for Correlation Heatmap"),
    dcc.Dropdown(
        id='dataset-selector',
        options=[
            {'label': 'Vehicle Registrations', 'value': 'vehicle'},
            {'label': 'Public Transport Usage', 'value': 'transport'},
            {'label': 'Bike Infrastructure', 'value': 'bike'}
        ],
        value='vehicle'
    ),
    
    # Dropdown to select columns for correlation heatmap
    html.Label("Select Columns for Correlation"),
    dcc.Dropdown(
        id='column-selector',
        multi=True,  # Allow selecting multiple columns
        placeholder="Select columns for correlation"
    ),

    # Dropdown to select color scale for the heatmap
    html.Label("Select Color Scale"),
    dcc.Dropdown(
        id='color-scale-selector',
        options=[
            {'label': 'Viridis', 'value': 'Viridis'},
            {'label': 'Cividis', 'value': 'Cividis'},
            {'label': 'Bluered', 'value': 'Bluered'},
            {'label': 'RdBu', 'value': 'RdBu'}
        ],
        value='Viridis'  # Default color scale
    ),

    # Correlation heatmap
    dcc.Graph(id='correlation-heatmap'),

    html.H2("Public Transport Usage Over Time"),
    # Public transport usage over time graph
    dcc.Graph(id='public-transport-graph'),

    html.H2("Vehicle Registrations by Postcode"),
    # Dropdown to select vehicle type for analysis
    dcc.Dropdown(
        id='vehicle-type-selector',
        options=[{'label': x, 'value': x} for x in vehicle_registration_df['CD_CL_FUEL_ENG'].unique()],
        value='All',
        placeholder="Select a vehicle type"
    ),
    dcc.Graph(id='vehicle-registrations-graph'),

    html.H2("Bike Infrastructure Distribution"),
    # Bike infrastructure map
    dcc.Graph(id='bike-infrastructure-map')
])

# Callback to update column options based on the selected dataset
@app.callback(
    Output('column-selector', 'options'),
    [Input('dataset-selector', 'value')]
)
def update_columns_options(selected_dataset):
    if selected_dataset == 'vehicle':
        return [{'label': col, 'value': col} for col in vehicle_registration_numeric.columns]
    elif selected_dataset == 'transport':
        return [{'label': col, 'value': col} for col in public_transport_numeric.columns]
    else:
        return [{'label': col, 'value': col} for col in bicycle_network_numeric.columns]

# Callback to update the correlation heatmap
@app.callback(
    Output('correlation-heatmap', 'figure'),
    [Input('dataset-selector', 'value'), Input('column-selector', 'value'), Input('color-scale-selector', 'value')]
)
def update_correlation_heatmap(selected_dataset, selected_columns, selected_color_scale):
    if selected_dataset == 'vehicle':
        df = vehicle_registration_numeric
    elif selected_dataset == 'transport':
        df = public_transport_numeric
    else:
        df = bicycle_network_numeric
    
    # If no columns selected, use all columns
    if not selected_columns:
        selected_columns = df.columns
    
    corr_matrix = df[selected_columns].corr()
    
    fig = ff.create_annotated_heatmap(
        z=corr_matrix.values,
        x=list(corr_matrix.columns),
        y=list(corr_matrix.index),
        colorscale=selected_color_scale,
        showscale=True
    )
    
    return fig

# Callback for Public Transport Usage Over Time
@app.callback(
    Output('public-transport-graph', 'figure'),
    [Input('dataset-selector', 'value')]
)
def update_public_transport_graph(selected_dataset):
    if 'Fin_year' not in public_transport_df.columns or 'Pax_annual' not in public_transport_df.columns:
        return px.line(title="Public Transport Data Missing or Incorrect")
    
    fig = px.line(public_transport_df, x='Fin_year', y='Pax_annual', title="Public Transport Usage Over Time")
    fig.update_layout(xaxis_title="Year", yaxis_title="Passenger Count")
    return fig

# Callback for Vehicle Registrations by Postcode
@app.callback(
    Output('vehicle-registrations-graph', 'figure'),
    [Input('vehicle-type-selector', 'value')]
)
def update_vehicle_registrations_graph(selected_vehicle_type):
    if selected_vehicle_type == 'All':
        df = vehicle_registration_df
    else:
        df = vehicle_registration_df[vehicle_registration_df['CD_CL_FUEL_ENG'] == selected_vehicle_type]
    
    if 'POSTCODE' not in df.columns or 'TOTAL1' not in df.columns:
        return px.bar(title="Vehicle Registration Data Missing or Incorrect")
    
    # Create the bar chart with custom colors
    fig = px.bar(
        df, 
        x='POSTCODE', 
        y='TOTAL1', 
        title=f"Vehicle Registrations for {selected_vehicle_type}",
        color_discrete_sequence=['#636EFA'],  # Custom color
        labels={'POSTCODE': 'Postcode', 'TOTAL1': 'Number of Vehicles'}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Postcode", 
        yaxis_title="Number of Vehicles",
        plot_bgcolor='#F9F9F9',  # Custom background color
        paper_bgcolor='#F9F9F9'
    )
    return fig

# Callback for Bike Infrastructure Map
@app.callback(
    Output('bike-infrastructure-map', 'figure'),
    [Input('dataset-selector', 'value')]
)
def update_bike_infrastructure_map(selected_dataset):
    if 'Latitude' not in bicycle_network_df.columns or 'Longitude' not in bicycle_network_df.columns:
        return px.scatter_mapbox(title="Bike Infrastructure Data Missing or Incorrect")
    
    fig = px.scatter_mapbox(
        bicycle_network_df, lat='Latitude', lon='Longitude',
        hover_name='local_name', hover_data=['facility_left', 'facility_right'],
        zoom=10, height=500
    )
    fig.update_layout(mapbox_style="open-street-map", title="Bike Infrastructure Distribution")
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

# # Import necessary libraries
# from dash import Dash, dcc, html
# from dash.dependencies import Input, Output
# import pandas as pd
# import plotly.express as px
# import plotly.figure_factory as ff

# # Initialize the Dash app
# app = Dash(__name__)

# # Load datasets
# vehicle_registration_df = pd.read_csv("C:\Datasets\Whole_Fleet_Vehicle_Registration_Snapshot_by_Postcode_Q2_2024.csv", low_memory=False)
# public_transport_df = pd.read_csv("C:\Datasets\Annual_Metropolitan_Train_Station_Entries_2023-24.csv", low_memory=False)
# bicycle_network_df = pd.read_csv("C:\Datasets\Principal_Bicycle_Network_(PBN).csv", low_memory=False)

# # Clean datasets by filling missing values
# vehicle_registration_df.fillna(0, inplace=True)
# public_transport_df.fillna(0, inplace=True)
# bicycle_network_df.fillna(0, inplace=True)

# # Filter numeric columns
# vehicle_registration_numeric = vehicle_registration_df.select_dtypes(include=['float64', 'int64'])
# public_transport_numeric = public_transport_df.select_dtypes(include=['float64', 'int64'])
# bicycle_network_numeric = bicycle_network_df.select_dtypes(include=['float64', 'int64'])

# # Dash layout with graphs and correlation heatmap
# app.layout = html.Div([
#     html.H1("Urban Transportation Insights Dashboard"),

#     # Dataset dropdown for correlation heatmap
#     html.Label("Select Dataset for Correlation Heatmap"),
#     dcc.Dropdown(
#         id='dataset-selector',
#         options=[
#             {'label': 'Vehicle Registrations', 'value': 'vehicle'},
#             {'label': 'Public Transport Usage', 'value': 'transport'},
#             {'label': 'Bike Infrastructure', 'value': 'bike'}
#         ],
#         value='vehicle'
#     ),
    
#     # Dropdown to select columns for correlation heatmap
#     html.Label("Select Columns for Correlation"),
#     dcc.Dropdown(
#         id='column-selector',
#         multi=True,  # Allow selecting multiple columns
#         placeholder="Select columns for correlation"
#     ),

#     # Dropdown to select color scale for the heatmap
#     html.Label("Select Color Scale"),
#     dcc.Dropdown(
#         id='color-scale-selector',
#         options=[
#             {'label': 'Viridis', 'value': 'Viridis'},
#             {'label': 'Cividis', 'value': 'Cividis'},
#             {'label': 'Bluered', 'value': 'Bluered'},
#             {'label': 'RdBu', 'value': 'RdBu'}
#         ],
#         value='Viridis'  # Default color scale
#     ),

#     # Correlation heatmap
#     dcc.Graph(id='correlation-heatmap'),

#     html.H2("Public Transport Usage Over Time"),
#     # Public transport usage over time graph
#     dcc.Graph(id='public-transport-graph'),

#     html.H2("Vehicle Registrations by Postcode"),
#     # Dropdown to select vehicle type for analysis
#     dcc.Dropdown(
#         id='vehicle-type-selector',
#         options=[{'label': x, 'value': x} for x in vehicle_registration_df['CD_CL_FUEL_ENG'].unique()],
#         value='All',
#         placeholder="Select a vehicle type"
#     ),
#     dcc.Graph(id='vehicle-registrations-graph'),

#     html.H2("Bike Infrastructure Distribution"),
#     # Bike infrastructure map
#     dcc.Graph(id='bike-infrastructure-map')
# ])

# # Callback to update column options based on the selected dataset
# @app.callback(
#     Output('column-selector', 'options'),
#     [Input('dataset-selector', 'value')]
# )
# def update_columns_options(selected_dataset):
#     if selected_dataset == 'vehicle':
#         return [{'label': col, 'value': col} for col in vehicle_registration_numeric.columns]
#     elif selected_dataset == 'transport':
#         return [{'label': col, 'value': col} for col in public_transport_numeric.columns]
#     else:
#         return [{'label': col, 'value': col} for col in bicycle_network_numeric.columns]

# # Callback to update the correlation heatmap
# @app.callback(
#     Output('correlation-heatmap', 'figure'),
#     [Input('dataset-selector', 'value'), Input('column-selector', 'value'), Input('color-scale-selector', 'value')]
# )
# def update_correlation_heatmap(selected_dataset, selected_columns, selected_color_scale):
#     if selected_dataset == 'vehicle':
#         df = vehicle_registration_numeric
#     elif selected_dataset == 'transport':
#         df = public_transport_numeric
#     else:
#         df = bicycle_network_numeric
    
#     # If no columns selected, use all columns
#     if not selected_columns:
#         selected_columns = df.columns
    
#     corr_matrix = df[selected_columns].corr()
    
#     fig = ff.create_annotated_heatmap(
#         z=corr_matrix.values,
#         x=list(corr_matrix.columns),
#         y=list(corr_matrix.index),
#         colorscale=selected_color_scale,
#         showscale=True
#     )
    
#     return fig

# # Callback for Public Transport Usage Over Time
# @app.callback(
#     Output('public-transport-graph', 'figure'),
#     [Input('dataset-selector', 'value')]
# )
# def update_public_transport_graph(selected_dataset):
#     if 'Fin_year' not in public_transport_df.columns or 'Pax_annual' not in public_transport_df.columns:
#         return px.line(title="Public Transport Data Missing or Incorrect")
    
#     fig = px.line(public_transport_df, x='Fin_year', y='Pax_annual', title="Public Transport Usage Over Time")
#     fig.update_layout(xaxis_title="Year", yaxis_title="Passenger Count")
#     return fig

# # Callback for Vehicle Registrations by Postcode
# @app.callback(
#     Output('vehicle-registrations-graph', 'figure'),
#     [Input('vehicle-type-selector', 'value')]
# )
# def update_vehicle_registrations_graph(selected_vehicle_type):
#     if selected_vehicle_type == 'All':
#         df = vehicle_registration_df
#     else:
#         df = vehicle_registration_df[vehicle_registration_df['CD_CL_FUEL_ENG'] == selected_vehicle_type]
    
#     if 'POSTCODE' not in df.columns or 'TOTAL1' not in df.columns:
#         return px.bar(title="Vehicle Registration Data Missing or Incorrect")
    
#     fig = px.bar(df, x='POSTCODE', y='TOTAL1', title=f"Vehicle Registrations for {selected_vehicle_type}")
#     fig.update_layout(xaxis_title="Postcode", yaxis_title="Number of Vehicles")
#     return fig

# # Callback for Bike Infrastructure Map
# @app.callback(
#     Output('bike-infrastructure-map', 'figure'),
#     [Input('dataset-selector', 'value')]
# )
# def update_bike_infrastructure_map(selected_dataset):
#     if 'Latitude' not in bicycle_network_df.columns or 'Longitude' not in bicycle_network_df.columns:
#         return px.scatter_mapbox(title="Bike Infrastructure Data Missing or Incorrect")
    
#     fig = px.scatter_mapbox(
#         bicycle_network_df, lat='Latitude', lon='Longitude',
#         hover_name='local_name', hover_data=['facility_left', 'facility_right'],
#         zoom=10, height=500
#     )
#     fig.update_layout(mapbox_style="open-street-map", title="Bike Infrastructure Distribution")
#     return fig


# #Import necessary libraries
# from dash import Dash, dcc, html
# from dash.dependencies import Input, Output
# import pandas as pd
# import plotly.express as px
# import plotly.figure_factory as ff

# # Initialize the Dash app
# app = Dash(__name__)
# # Import necessary libraries
# from dash import Dash, dcc, html
# from dash.dependencies import Input, Output
# import pandas as pd
# import plotly.express as px

# # Initialize the Dash app
# app = Dash(__name__)

# # Load datasets without any dtype specification
# vehicle_registration_df = pd.read_csv("C:\Datasets\Whole_Fleet_Vehicle_Registration_Snapshot_by_Postcode_Q2_2024.csv", low_memory=False)
# public_transport_df = pd.read_csv("C:\Datasets\Annual_Metropolitan_Train_Station_Entries_2023-24.csv" , low_memory=False)
# bicycle_network_df = pd.read_csv("C:\Datasets\principal_Bicycle_Network_(PBN).csv", low_memory=False)
# journey_to_work_df = pd.read_csv("C:\Datasets\JourneyToWork_VISTA_1220_LGA_V1.csv", low_memory=False)

# # Step 1: Cleaning Vehicle Registration Data
# vehicle_registration_df['CD_MAKE_VEH1'].fillna('Unknown', inplace=True)
# vehicle_registration_df['CD_CL_FUEL_ENG'].fillna('Unknown', inplace=True)
# vehicle_registration_df['TOTAL1'].fillna(0, inplace=True)

# # Step 2: Cleaning Public Transport Data
# public_transport_df['Pax_annual'].fillna(0, inplace=True)
# public_transport_df['St
# # Load datasets with error handling
# try:
#     vehicle_registration_df = pd.read_csv("C:\Datasets\Whole_Fleet_Vehicle_Registration_Snapshot_by_Postcode_Q2_2024.csv", low_memory=False)
#     public_transport_df = pd.read_csv("C:\Datasets\Annual_Metropolitan_Train_Station_Entries_2023-24.csv", low_memory=False)
#     bicycle_network_df = pd.read_csv("C:\Datasets\Principal_Bicycle_Network_(PBN).csv", low_memory=False)
# except FileNotFoundError as e:
#     print(f"Error loading CSV files: {e}")
#     vehicle_registration_df = pd.DataFrame()
#     public_transport_df = pd.DataFrame()
#     bicycle_network_df = pd.DataFrame()

# # Clean datasets by filling missing values
# vehicle_registration_df.fillna(0, inplace=True)
# public_transport_df.fillna(0, inplace=True)
# bicycle_network_df.fillna(0, inplace=True)

# # Filter numeric columns for correlation heatmap
# vehicle_registration_numeric = vehicle_registration_df.select_dtypes(include=['float64', 'int64'])
# public_transport_numeric = public_transport_df.select_dtypes(include=['float64', 'int64'])
# bicycle_network_numeric = bicycle_network_df.select_dtypes(include=['float64', 'int64'])

# # Define available color scales
# color_scales = ['Viridis', 'Cividis', 'Bluered', 'RdBu']

# # Dash layout with organized sections
# app.layout = html.Div([
#     html.H1("Urban Transportation Insights Dashboard"),
    
    # html.Div([
    #     html.H2("Correlation Heatmap"),
        
    #     # Dataset dropdown for correlation heatmap
    #     html.Label("Select Dataset"),
    #     dcc.Dropdown(
    #         id='dataset-selector',
    #         options=[
    #             {'label': 'Vehicle Registrations', 'value': 'vehicle'},
    #             {'label': 'Public Transport Usage', 'value': 'transport'},
    #             {'label': 'Bike Infrastructure', 'value': 'bike'}
    #         ],
    #         value='vehicle'
    #     ),
        
    #     # Dropdown to select columns for correlation heatmap
    #     html.Label("Select Columns for Correlation"),
    #     dcc.Dropdown(
    #         id='column-selector',
    #         multi=True,  # Allow selecting multiple columns
    #         placeholder="Select columns for correlation"
    #     ),
    
    #     # Dropdown to select color scale for the heatmap
    #     html.Label("Select Color Scale"),
    #     dcc.Dropdown(
    #         id='color-scale-selector',
    #         options=[{'label': scale, 'value': scale} for scale in color_scales],
    #         value='Viridis'  # Default color scale
    #     ),
    
    #     # Correlation heatmap
    #     dcc.Graph(id='correlation-heatmap'),
    # ], style={'padding': '20px', 'border': '1px solid #ccc', 'margin-bottom': '20px'}),
    
#     html.Div([
#         html.H2("Public Transport Usage Over Time"),
#         # Public transport usage over time graph
#         dcc.Graph(id='public-transport-graph'),
#     ], style={'padding': '20px', 'border': '1px solid #ccc', 'margin-bottom': '20px'}),
    
#     html.Div([
#         html.H2("Vehicle Registrations by Postcode"),
#         # Dropdown to select vehicle type for analysis
#         html.Label("Select Vehicle Type"),
#         dcc.Dropdown(
#             id='vehicle-type-selector',
#             options=[{'label': x, 'value': x} for x in sorted(vehicle_registration_df['CD_CL_FUEL_ENG'].unique())] + [{'label': 'All', 'value': 'All'}],
#             value='All',
#             placeholder="Select a vehicle type"
#         ),
#         dcc.Graph(id='vehicle-registrations-graph'),
#     ], style={'padding': '20px', 'border': '1px solid #ccc', 'margin-bottom': '20px'}),
    
#     html.Div([
#         html.H2("Bike Infrastructure Distribution"),
#         # Bike infrastructure map
#         dcc.Graph(id='bike-infrastructure-map'),
#     ], style={'padding': '20px', 'border': '1px solid #ccc', 'margin-bottom': '20px'}),
# ])

# # Callback to update column options based on the selected dataset
# @app.callback(
#     Output('column-selector', 'options'),
#     [Input('dataset-selector', 'value')]
# )
# def update_columns_options(selected_dataset):
#     if selected_dataset == 'vehicle':
#         columns = vehicle_registration_numeric.columns
#     elif selected_dataset == 'transport':
#         columns = public_transport_numeric.columns
#     elif selected_dataset == 'bike':
#         columns = bicycle_network_numeric.columns
#     else:
#         columns = []
#     return [{'label': col, 'value': col} for col in columns]

# # Callback to update the correlation heatmap
# @app.callback(
#     Output('correlation-heatmap', 'figure'),
#     [Input('dataset-selector', 'value'), Input('column-selector', 'value'), Input('color-scale-selector', 'value')]
# )
# def update_correlation_heatmap(selected_dataset, selected_columns, selected_color_scale):
#     if selected_dataset == 'vehicle':
#         df = vehicle_registration_numeric
#     elif selected_dataset == 'transport':
#         df = public_transport_numeric
#     elif selected_dataset == 'bike':
#         df = bicycle_network_numeric
#     else:
#         df = pd.DataFrame()
    
#     # If no columns selected, use all columns
#     if selected_columns and len(selected_columns) > 1:
#         corr_matrix = df[selected_columns].corr()
#     else:
#         corr_matrix = df.corr()
    
#     if corr_matrix.empty:
#         return {
#             'data': [],
#             'layout': {
#                 'title': 'No data available for the selected options.'
#             }
#         }
    
#     fig = ff.create_annotated_heatmap(
#         z=corr_matrix.values,
#         x=list(corr_matrix.columns),
#         y=list(corr_matrix.index),
#         colorscale=selected_color_scale,
#         showscale=True
#     )
    
#     fig.update_layout(
#         title='Correlation Heatmap',
#         xaxis_title='Variables',
#         yaxis_title='Variables',
#         height=600
#     )
    
#     return fig

# # Callback for Public Transport Usage Over Time
# @app.callback(
#     Output('public-transport-graph', 'figure'),
#     [Input('public-transport-graph', 'id')]  # Dummy input to trigger on load
# )
# def update_public_transport_graph(_):
#     if 'Fin_year' not in public_transport_df.columns or 'Pax_annual' not in public_transport_df.columns:
#         return {
#             'data': [],
#             'layout': {
#                 'title': 'Required columns are missing in the Public Transport dataset.'
#             }
#         }
#     # Ensure that 'Fin_year' is sorted and treated as a categorical or datetime if necessary
#     fig = px.line(public_transport_df, x='Fin_year', y='Pax_annual', title="Public Transport Usage Over Time")
#     fig.update_layout(xaxis_title="Year", yaxis_title="Passenger Count")
#     return fig

# # Callback for Vehicle Registrations by Postcode
# @app.callback(
#     Output('vehicle-registrations-graph', 'figure'),
#     [Input('vehicle-type-selector', 'value')]
# )
# def update_vehicle_registrations_graph(selected_vehicle_type):
#     if 'CD_CL_FUEL_ENG' not in vehicle_registration_df.columns or 'POSTCODE' not in vehicle_registration_df.columns or 'TOTAL1' not in vehicle_registration_df.columns:
#         return {
#             'data': [],
#             'layout': {
#                 'title': 'Required columns are missing in the Vehicle Registration dataset.'
#             }
#         }
    
#     if selected_vehicle_type == 'All':
#         df = vehicle_registration_df
#         title = "All Vehicle Registrations by Postcode"
#     else:
#         df = vehicle_registration_df[vehicle_registration_df['CD_CL_FUEL_ENG'] == selected_vehicle_type]
#         title = f"Vehicle Registrations for {selected_vehicle_type} by Postcode"
    
#     if df.empty:
#         return {
#             'data': [],
#             'layout': {
#                 'title': f'No data available for {selected_vehicle_type}.'
#             }
#         }
    
#     # Aggregate registrations by postcode
#     df_agg = df.groupby('POSTCODE')['TOTAL1'].sum().reset_index()
    
#     fig = px.bar(df_agg, x='POSTCODE', y='TOTAL1', title=title)
#     fig.update_layout(xaxis_title="Postcode", yaxis_title="Number of Vehicles", xaxis={'categoryorder':'total descending'})
#     return fig

# # Callback for Bike Infrastructure Map
# @app.callback(
#     Output('bike-infrastructure-map', 'figure'),
#     [Input('bike-infrastructure-map', 'id')]  # Dummy input to trigger on load
# )
# def update_bike_infrastructure_map(_):
#     required_columns = ['Latitude', 'Longitude', 'local_name']
#     if not all(col in bicycle_network_df.columns for col in required_columns):
#         return {
#             'data': [],
#             'layout': {
#                 'title': 'Required columns are missing in the Bike Infrastructure dataset.'
#             }
#         }
    
#     # Drop rows with missing coordinates
#     df_map = bicycle_network_df.dropna(subset=['Latitude', 'Longitude'])
    
#     if df_map.empty:
#         return {
#             'data': [],
#             'layout': {
#                 'title': 'No location data available for Bike Infrastructure.'
#             }
#         }
    
#     fig = px.scatter_mapbox(
#         df_map, lat='Latitude', lon='Longitude',
#         hover_name='local_name',
#         hover_data=['facility_left', 'facility_right'],
#         zoom=10, height=500,
#         title="Bike Infrastructure Distribution"
#     )
#     fig.update_layout(mapbox_style="open-street-map")
#     fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
#     return fig

# # Run the app
# if __name__ == '__main__':
#     app.run_server(debug=True)

# # Import necessary libraries
# from dash import Dash, dcc, html
# from dash.dependencies import Input, Output
# import pandas as pd
# import plotly.express as px
# import plotly.figure_factory as ff

# # Initialize the Dash app
# app = Dash(__name__)

# # Load datasets
# vehicle_registration_df = pd.read_csv("C:\Datasets\Whole_Fleet_Vehicle_Registration_Snapshot_by_Postcode_Q2_2024.csv", low_memory=False)
# public_transport_df = pd.read_csv("C:\Datasets\Annual_Metropolitan_Train_Station_Entries_2023-24.csv", low_memory=False)
# bicycle_network_df = pd.read_csv("C:\Datasets\Principal_Bicycle_Network_(PBN).csv", low_memory=False)

# # Clean datasets by filling missing values
# vehicle_registration_df.fillna(0, inplace=True)
# public_transport_df.fillna(0, inplace=True)
# bicycle_network_df.fillna(0, inplace=True)

# # Filter numeric columns
# vehicle_registration_numeric = vehicle_registration_df.select_dtypes(include=['float64', 'int64'])
# public_transport_numeric = public_transport_df.select_dtypes(include=['float64', 'int64'])
# bicycle_network_numeric = bicycle_network_df.select_dtypes(include=['float64', 'int64'])

# # Dash layout with graphs and correlation heatmap
# app.layout = html.Div([
#     html.H1("Urban Transportation Insights Dashboard"),

#     # Dataset dropdown for correlation heatmap
#     html.Label("Select Dataset for Correlation Heatmap"),
#     dcc.Dropdown(
#         id='dataset-selector',
#         options=[
#             {'label': 'Vehicle Registrations', 'value': 'vehicle'},
#             {'label': 'Public Transport Usage', 'value': 'transport'},
#             {'label': 'Bike Infrastructure', 'value': 'bike'}
#         ],
#         value='vehicle'
#     ),
    
#     # Dropdown to select columns for correlation heatmap
#     html.Label("Select Columns for Correlation"),
#     dcc.Dropdown(
#         id='column-selector',
#         multi=True,  # Allow selecting multiple columns
#         placeholder="Select columns for correlation"
#     ),

#     # Dropdown to select color scale for the heatmap
#     html.Label("Select Color Scale"),
#     dcc.Dropdown(
#         id='color-scale-selector',
#         options=[
#             {'label': 'Viridis', 'value': 'Viridis'},
#             {'label': 'Cividis', 'value': 'Cividis'},
#             {'label': 'Bluered', 'value': 'Bluered'},
#             {'label': 'RdBu', 'value': 'RdBu'}
#         ],
#         value='Viridis'  # Default color scale
#     ),

#     # Correlation heatmap
#     dcc.Graph(id='correlation-heatmap'),

#     html.H2("Public Transport Usage Over Time"),
#     # Public transport usage over time graph
#     dcc.Graph(id='public-transport-graph'),

#     html.H2("Vehicle Registrations by Postcode"),
#     # Dropdown to select vehicle type for analysis
#     dcc.Dropdown(
#         id='vehicle-type-selector',
#         options=[{'label': x, 'value': x} for x in vehicle_registration_df['CD_CL_FUEL_ENG'].unique()],
#         value='All',
#         placeholder="Select a vehicle type"
#     ),
#     dcc.Graph(id='vehicle-registrations-graph'),

#     html.H2("Bike Infrastructure Distribution"),
#     # Bike infrastructure map
#     dcc.Graph(id='bike-infrastructure-map')
# ])

# # Callback to update column options based on the selected dataset
# @app.callback(
#     Output('column-selector', 'options'),
#     [Input('dataset-selector', 'value')]
# )
# def update_columns_options(selected_dataset):
#     if selected_dataset == 'vehicle':
#         return [{'label': col, 'value': col} for col in vehicle_registration_numeric.columns]
#     elif selected_dataset == 'transport':
#         return [{'label': col, 'value': col} for col in public_transport_numeric.columns]
#     else:
#         return [{'label': col, 'value': col} for col in bicycle_network_numeric.columns]

# # Callback to update the correlation heatmap
# @app.callback(
#     Output('correlation-heatmap', 'figure'),
#     [Input('dataset-selector', 'value'), Input('column-selector', 'value'), Input('color-scale-selector', 'value')]
# )
# def update_correlation_heatmap(selected_dataset, selected_columns, selected_color_scale):
#     if selected_dataset == 'vehicle':
#         df = vehicle_registration_numeric
#     elif selected_dataset == 'transport':
#         df = public_transport_numeric
#     else:
#         df = bicycle_network_numeric
    
#     # If no columns selected, use all columns
#     if not selected_columns:
#         selected_columns = df.columns
    
#     corr_matrix = df[selected_columns].corr()
    
#     fig = ff.create_annotated_heatmap(
#         z=corr_matrix.values,
#         x=list(corr_matrix.columns),
#         y=list(corr_matrix.index),
#         colorscale=selected_color_scale,
#         showscale=True
#     )
    
#     return fig

# # Callback for Public Transport Usage Over Time
# @app.callback(
#     Output('public-transport-graph', 'figure'),
#     [Input('dataset-selector', 'value')]
# )
# def update_public_transport_graph(selected_dataset):
#     fig = px.line(public_transport_df, x='Fin_year', y='Pax_annual', title="Public Transport Usage Over Time")
#     fig.update_layout(xaxis_title="Year", yaxis_title="Passenger Count")
#     return fig

# # Callback for Vehicle Registrations by Postcode
# @app.callback(
#     Output('vehicle-registrations-graph', 'figure'),
#     [Input('vehicle-type-selector', 'value')]
# )
# def update_vehicle_registrations_graph(selected_vehicle_type):
#     if selected_vehicle_type == 'All':
#         df = vehicle_registration_df
#     else:
#         df = vehicle_registration_df[vehicle_registration_df['CD_CL_FUEL_ENG'] == selected_vehicle_type]
    
#     fig = px.bar(df, x='POSTCODE', y='TOTAL1', title=f"Vehicle Registrations for {selected_vehicle_type}")
#     fig.update_layout(xaxis_title="Postcode", yaxis_title="Number of Vehicles")
#     return fig

# # Callback for Bike Infrastructure Map
# @app.callback(
#     Output('bike-infrastructure-map', 'figure'),
#     [Input('dataset-selector', 'value')]
# )
# def update_bike_infrastructure_map(selected_dataset):
#     fig = px.scatter_mapbox(
#         bicycle_network_df, lat='Latitude', lon='Longitude',
#         hover_name='local_name', hover_data=['facility_left', 'facility_right'],
#         zoom=10, height=500
#     )
#     fig.update_layout(mapbox_style="open-street-map", title="Bike Infrastructure Distribution")
#     return fig

# # Run the app
# if __name__ == '__main__':
#     app.run_server(debug=True)


# Import necessary libraries
# from dash import Dash, dcc, html
# from dash.dependencies import Input, Output
# import pandas as pd
# import plotly.figure_factory as ff

# # Initialize the Dash app
# app = Dash(__name__)

# # Load datasets
# vehicle_registration_df = pd.read_csv("C:\Datasets\Whole_Fleet_Vehicle_Registration_Snapshot_by_Postcode_Q2_2024.csv", low_memory=False)
# public_transport_df = pd.read_csv("C:\Datasets\Annual_Metropolitan_Train_Station_Entries_2023-24.csv", low_memory=False)
# bicycle_network_df = pd.read_csv("C:\Datasets\Principal_Bicycle_Network_(PBN).csv", low_memory=False)

# # Clean datasets by filling missing values
# vehicle_registration_df.fillna(0, inplace=True)
# public_transport_df.fillna(0, inplace=True)
# bicycle_network_df.fillna(0, inplace=True)

# # Filter numeric columns
# vehicle_registration_numeric = vehicle_registration_df.select_dtypes(include=['float64', 'int64'])
# public_transport_numeric = public_transport_df.select_dtypes(include=['float64', 'int64'])
# bicycle_network_numeric = bicycle_network_df.select_dtypes(include=['float64', 'int64'])

# # Layout for Dash app
# app.layout = html.Div([
#     html.H1("Enhanced Correlation Heatmap"),

#     # Dataset dropdown
#     html.Label("Select Dataset"),
#     dcc.Dropdown(
#         id='dataset-selector',
#         options=[
#             {'label': 'Vehicle Registrations', 'value': 'vehicle'},
#             {'label': 'Public Transport Usage', 'value': 'transport'},
#             {'label': 'Bike Infrastructure', 'value': 'bike'}
#         ],
#         value='vehicle'
#     ),
    
#     # Dropdown to select columns for correlation heatmap
#     html.Label("Select Columns for Correlation"),
#     dcc.Dropdown(
#         id='column-selector',
#         multi=True,  # Allow selecting multiple columns
#         placeholder="Select columns for correlation"
#     ),

#     # Dropdown to select color scale for the heatmap
#     html.Label("Select Color Scale"),
#     dcc.Dropdown(
#         id='color-scale-selector',
#         options=[
#             {'label': 'Viridis', 'value': 'Viridis'},
#             {'label': 'Cividis', 'value': 'Cividis'},
#             {'label': 'Bluered', 'value': 'Bluered'},
#             {'label': 'RdBu', 'value': 'RdBu'}
#         ],
#         value='Viridis'  # Default color scale
#     ),

#     # Correlation heatmap
#     dcc.Graph(id='correlation-heatmap')
# ])

# # Callback to update column options based on the selected dataset
# @app.callback(
#     Output('column-selector', 'options'),
#     [Input('dataset-selector', 'value')]
# )
# def update_columns_options(selected_dataset):
#     if selected_dataset == 'vehicle':
#         return [{'label': col, 'value': col} for col in vehicle_registration_numeric.columns]
#     elif selected_dataset == 'transport':
#         return [{'label': col, 'value': col} for col in public_transport_numeric.columns]
#     else:
#         return [{'label': col, 'value': col} for col in bicycle_network_numeric.columns]

# # Callback to update the correlation heatmap
# @app.callback(
#     Output('correlation-heatmap', 'figure'),
#     [Input('dataset-selector', 'value'), Input('column-selector', 'value'), Input('color-scale-selector', 'value')]
# )
# def update_correlation_heatmap(selected_dataset, selected_columns, selected_color_scale):
#     if selected_dataset == 'vehicle':
#         df = vehicle_registration_numeric
#     elif selected_dataset == 'transport':
#         df = public_transport_numeric
#     else:
#         df = bicycle_network_numeric
    
#     # If no columns selected, use all columns
#     if not selected_columns:
#         selected_columns = df.columns
    

#     # Create the heatmap
#     fig = ff.create_annotated_heatmap(
#         z=corr_matrix.values,
#         x=list(corr_matrix.columns),
#         y=list(corr_matrix.index),
#         colorscale=selected_color_scale,
#         showscale=True
#     )
    
#     return fig

# # Run the app
# if __name__ == '__main__':
#     app.run_server(debug=True)



# # Import necessary libraries
# from dash import Dash, dcc, html
# from dash.dependencies import Input, Output
# import pandas as pd
# import plotly.figure_factory as ff
# import plotly.express as px

# # Initialize the Dash app
# app = Dash(__name__)

# # Load the vehicle registration dataset
# vehicle_registration_df = pd.read_csv("C:\Datasets\Whole_Fleet_Vehicle_Registration_Snapshot_by_Postcode_Q2_2024.csv", low_memory=False)

# # Ensure the dataset is clean before calculating the correlation matrix
# vehicle_registration_df.fillna(0, inplace=True)  # Fill missing numeric values

# # Filter only numeric columns for correlation
# vehicle_registration_numeric = vehicle_registration_df.select_dtypes(include=['float64', 'int64'])

# # Simplified Dash layout including only the correlation heatmap
# app.layout = html.Div([
#     html.H1("Vehicle Registration Correlation Heatmap"),
    
#     # Correlation heatmap placeholder
#     dcc.Graph(id='correlation-heatmap')
# ])

# # Correlation Heatmap callback
# @app.callback(
#     Output('correlation-heatmap', 'figure'),
#     [Input('correlation-heatmap', 'id')]  # Dummy input to trigger the callback
# )
# def update_correlation_heatmap(_):
#     # Calculate the correlation matrix for numeric columns in vehicle registration data
#     corr_matrix = vehicle_registration_numeric.corr()
    
#     # Create annotated heatmap
#     fig = ff.create_annotated_heatmap(
#         z=corr_matrix.values,
#         x=list(corr_matrix.columns),
#         y=list(corr_matrix.index),
#         colorscale='Viridis',
#         showscale=True
#     )
#     return fig

# # Run the app
# if __name__ == '__main__':
#     app.run_server(debug=True)


# # Import necessary libraries
# from dash import Dash, dcc, html
# from dash.dependencies import Input, Output
# import pandas as pd
# import plotly.express as px

# # Initialize the Dash app
# app = Dash(__name__)

# # Load datasets without any dtype specification
# vehicle_registration_df = pd.read_csv("C:\Datasets\Whole_Fleet_Vehicle_Registration_Snapshot_by_Postcode_Q2_2024.csv", low_memory=False)
# public_transport_df = pd.read_csv("C:\Datasets\Annual_Metropolitan_Train_Station_Entries_2023-24.csv", low_memory=False)
# bicycle_network_df = pd.read_csv("C:\Datasets\Principal_Bicycle_Network_(PBN).csv", low_memory=False)
# journey_to_work_df = pd.read_csv("C:\Datasets\JourneyToWork_VISTA_1220_LGA_V1.csv", low_memory=False)

# # Example of showing the first few rows of each dataset for debugging
# print(vehicle_registration_df.head())
# print(public_transport_df.head())
# print(bicycle_network_df.head())
# print(journey_to_work_df.head())

# # Step 1: Cleaning Vehicle Registration Data

# # Fill missing values in categorical columns with 'Unknown'
# vehicle_registration_df['CD_MAKE_VEH1'].fillna('Unknown', inplace=True)
# vehicle_registration_df['CD_CL_FUEL_ENG'].fillna('Unknown', inplace=True)

# # For numeric columns, fill missing values with 0
# vehicle_registration_df['TOTAL1'].fillna(0, inplace=True)

# # Debugging: Show the first few rows of cleaned vehicle registration data
# print(vehicle_registration_df.head())

# # Step 2: Cleaning Public Transport Data

# # For this dataset, ensure that missing numeric values are filled with 0
# public_transport_df['Pax_annual'].fillna(0, inplace=True)

# # Fill missing values in categorical columns with 'Unknown'
# public_transport_df['Stop_name'].fillna('Unknown', inplace=True)

# # Debugging: Show the first few rows of cleaned public transport data
# print(public_transport_df.head())

# # Step 3: Cleaning Bicycle Network Data

# # Fill missing values in string columns with 'Unknown'
# bicycle_network_df['local_name'].fillna('Unknown', inplace=True)
# bicycle_network_df['local_type'].fillna('Unknown', inplace=True)
# bicycle_network_df['name'].fillna('Unknown', inplace=True)
# bicycle_network_df['side'].fillna('Unknown', inplace=True)
# bicycle_network_df['facility_left'].fillna('Unknown', inplace=True)
# bicycle_network_df['surface_left'].fillna('Unknown', inplace=True)
# bicycle_network_df['facility_right'].fillna('Unknown', inplace=True)
# bicycle_network_df['surface_right'].fillna('Unknown', inplace=True)
# bicycle_network_df['lighting'].fillna('Unknown', inplace=True)
# bicycle_network_df['verified_date'].fillna('Unknown', inplace=True)
# bicycle_network_df['scc_name'].fillna('Unknown', inplace=True)
# bicycle_network_df['comments'].fillna('Unknown', inplace=True)

# # Fill missing numeric columns with 0
# bicycle_network_df['rd_num'].fillna(0, inplace=True)
# bicycle_network_df['width_left'].fillna(0, inplace=True)
# bicycle_network_df['width_right'].fillna(0, inplace=True)
# bicycle_network_df['bearing'].fillna(0, inplace=True)

# # Debugging: Show the first few rows of cleaned bicycle network data
# print(bicycle_network_df.head())
# # Step 4: Cleaning Journey to Work Data

# # Fill missing values in numeric columns with 0
# journey_to_work_df['time10'].fillna(0, inplace=True)
# journey_to_work_df['time11'].fillna(0, inplace=True)
# journey_to_work_df['time12'].fillna(0, inplace=True)
# journey_to_work_df['wdjtwwgt_LGA'].fillna(0, inplace=True)
# journey_to_work_df['wejtwwgt_LGA'].fillna(0, inplace=True)

# # Fill missing values in string columns with 'Unknown'
# journey_to_work_df['jtwid'].fillna('Unknown', inplace=True)
# journey_to_work_df['persid'].fillna('Unknown', inplace=True)
# journey_to_work_df['hhid'].fillna('Unknown', inplace=True)

# # Debugging: Show the first few rows of cleaned journey to work data
# print(journey_to_work_df.head())

# # Dash layout with a correlation heatmap component added
# app.layout = html.Div([
#     html.H1("Urban Transportation Insights"),
    
#     dcc.Dropdown(
#         id='data-selector',
#         options=[
#             {'label': 'Public Transport Usage', 'value': 'transport'},
#             {'label': 'Vehicle Registrations', 'value': 'vehicle'},
#             {'label': 'Bike Infrastructure', 'value': 'bike'}
#         ],
#         value='transport'
#     ),
    
#     # Add the correlation heatmap placeholder in the layout
#     dcc.Graph(id='correlation-heatmap'),
    
#     # Main graph to show public transport, vehicles, or bike infrastructure
#     dcc.Graph(id='main-graph')
# ])

# # Dummy callback for basic visualization
# @app.callback(
#     Output('main-graph', 'figure'),
#     [Input('data-selector', 'value')]
# )
# def update_graph(selected_data):
#     if selected_data == 'transport':
#         fig = px.bar(public_transport_df.head(10), x='Stop_ID', y='Pax_annual', title='Public Transport Usage')
#     elif selected_data == 'vehicle':
#         fig = px.bar(vehicle_registration_df.head(10), x='POSTCODE', y='TOTAL1', title='Vehicle Registrations')
#     else:
#         fig = px.scatter(bicycle_network_df.head(10), x='objectid', y='rd_num', title='Bike Infrastructure')
#     return fig

# # Correlation Heatmap callback
# @app.callback(
#     Output('correlation-heatmap', 'figure'),
#     [Input('data-selector', 'value')]
# )
# def update_correlation_heatmap(selected_data):
#     if selected_data == 'vehicle':
#         corr_matrix = vehicle_registration_df.corr()  # Calculate correlation matrix
#         fig = ff.create_annotated_heatmap(
#             z=corr_matrix.values,
#             x=list(corr_matrix.columns),
#             y=list(corr_matrix.index),
#             colorscale='Viridis',
#             showscale=True
#         )
#         return fig

# # Run the app
# if __name__ == '__main__':
#     app.run_server(debug=True)

# # Import necessary libraries
# from dash import Dash, dcc, html
# from dash.dependencies import Input, Output
# import pandas as pd
# import plotly.express as px
# import plotly.figure_factory as ff
# import geopandas as gpd

# # Initialize the Dash app
# app = Dash(__name__)

# # Load datasets with explicit dtype specification for problematic columns

# # Vehicle Registration Dataset
# vehicle_registration_df = pd.read_csv("C:\DataSets\Whole_Fleet_Vehicle_Registration_Snapshot_by_Postcode_Q2_2024.csv", 
#                                       low_memory=False, 
#                                       dtype={
#                                           'CD_MAKE_VEH1': 'object',  # Treat as string
#                                           'CD_CLASS_VEH': 'int64',   # Integer for vehicle class
#                                           'NB_YEAR_MFC_VEH': 'int64',# Integer for year
#                                           'POSTCODE': 'int64',       # Integer for postcode
#                                           'CD_CL_FUEL_ENG': 'object',# Fuel type as string
#                                           'TOTAL1': 'int64'          # Integer for total vehicles
#                                       })

# # Public Transport Dataset
# public_transport_df = pd.read_csv("C:\Datasets\Annual_Metropolitan_Train_Station_Entries_2023-24.csv", 
#                                   low_memory=False, 
#                                   dtype={
#                                       'Fin_year': 'object',         # Financial year as string
#                                       'Stop_ID': 'int64',           # Stop ID as integer
#                                       'Stop_name': 'object',        # Stop name as string
#                                       'Stop_lat': 'float64',        # Latitude as float
#                                       'Stop_long': 'float64',       # Longitude as float
#                                       'Pax_annual': 'int64'         # Annual passenger count as integer
#                                   })

# # Bicycle Network Dataset (Cleaned)
# bicycle_network_df = pd.read_csv("C:\Datasets\Principal_Bicycle_Network_(PBN).csv", 
#                                  low_memory=False, 
#                                  dtype={
#                                      'objectid': 'int64',  
#                                      'network': 'object',
#                                      'type': 'object',    
#                                      'status': 'object',  
#                                      'strategic_cycling_corridor': 'object', 
#                                      'local_name': 'object', 
#                                      'local_type': 'object', 
#                                      'rd_num': 'float64',   
#                                      'name': 'object',      
#                                      'side': 'object',      
#                                      'facility_left': 'object', 
#                                      'surface_left': 'object',
#                                      'width_left': 'float64',  
#                                      'facility_right': 'object',
#                                      'surface_right': 'object',
#                                      'width_right': 'float64',
#                                      'lighting': 'object', 
#                                      'verified_date': 'object',
#                                      'bearing': 'float64',
#                                      'scc_name': 'object',   
#                                      'comments': 'object'
#                                  })

# # Clean missing values in the bicycle network dataset
# bicycle_network_df['local_name'].fillna('Unknown', inplace=True)
# bicycle_network_df['local_type'].fillna('Unknown', inplace=True)
# bicycle_network_df['name'].fillna('Unknown', inplace=True)
# bicycle_network_df['side'].fillna('Unknown', inplace=True)
# bicycle_network_df['facility_left'].fillna('Unknown', inplace=True)
# bicycle_network_df['surface_left'].fillna('Unknown', inplace=True)
# bicycle_network_df['facility_right'].fillna('Unknown', inplace=True)
# bicycle_network_df['surface_right'].fillna('Unknown', inplace=True)
# bicycle_network_df['lighting'].fillna('Unknown', inplace=True)
# bicycle_network_df['verified_date'].fillna('Unknown', inplace=True)
# bicycle_network_df['scc_name'].fillna('Unknown', inplace=True)
# bicycle_network_df['comments'].fillna('Unknown', inplace=True)

# bicycle_network_df['rd_num'].fillna(0, inplace=True)
# bicycle_network_df['width_left'].fillna(0, inplace=True)
# bicycle_network_df['width_right'].fillna(0, inplace=True)
# bicycle_network_df['bearing'].fillna(0, inplace=True)

# # Journey to Work Dataset (Cleaned)
# journey_to_work_df = pd.read_csv("C:\Datasets\JourneyToWork_VISTA_1220_LGA_V1.csv", 
#                                  low_memory=False, 
#                                  dtype={
#                                      'jtwid': 'object',             
#                                      'persid': 'object',            
#                                      'hhid': 'object',              
#                                      'jtwtraveltime': 'int64',      
#                                      'jtw_at': 'int64',             
#                                      'time10': 'float64',           
#                                      'time11': 'float64',           
#                                      'time12': 'float64',           
#                                      'wdjtwwgt_LGA': 'float64',     
#                                      'wejtwwgt_LGA': 'float64'      
#                                  })

# # Clean missing values in the journey to work dataset
# journey_to_work_df['time10'].fillna(0, inplace=True)
# journey_to_work_df['time11'].fillna(0, inplace=True)
# journey_to_work_df['time12'].fillna(0, inplace=True)
# journey_to_work_df['wdjtwwgt_LGA'].fillna(0, inplace=True)
# journey_to_work_df['wejtwwgt_LGA'].fillna(0, inplace=True)

# Ensure columns with mixed types are handled as strings
# This will prevent further dtype warnings due to mixed data types in some columns

# The rest of the app layout and callback code continues here...

# Data Preparation for Visualization

# # Example: Prepare data for peak transport usage
# peak_columns = ['Pax_annual']
# peak_transport_usage = public_transport_df[peak_columns].sum().reset_index()
# peak_transport_usage.columns = ['Peak Period', 'Passenger Count']
# peak_transport_usage = peak_transport_usage.sort_values(by='Passenger Count', ascending=False)

# # Example: Data preparation for carbon emissions based on vehicle registrations
# emission_factors = {'P': 0.24, 'D': 0.26, 'E': 0.00}
# vehicle_registration_df['Emission Factor'] = vehicle_registration_df['CD_CL_FUEL_ENG'].map(emission_factors)
# vehicle_registration_df['Estimated Emissions'] = vehicle_registration_df['TOTAL1'] * vehicle_registration_df['Emission Factor']

# # Dash layout
# app.layout = html.Div([
#     html.H1("Urban Transportation Insights"),

#     # Dropdown for selecting dataset
#     dcc.Dropdown(
#         id='data-selector',
#         options=[
#             {'label': 'Public Transport Usage', 'value': 'transport'},
#             {'label': 'Vehicle Registrations', 'value': 'vehicle'},
#             {'label': 'Private Vehicle Commutes', 'value': 'private_vehicle'},
#             {'label': 'Bike Infrastructure', 'value': 'bike'}
#         ],
#         value='transport'
#     ),

#     # Graph for transport usage, vehicle registrations, etc.
#     dcc.Graph(id='main-graph'),

#     # Pie chart for carbon emissions by fuel type
#     dcc.Graph(id='emission-pie-chart'),

#     # Correlation heatmap for vehicle registration
#     dcc.Graph(id='correlation-heatmap'),

#     # Geospatial map for biking infrastructure
#     dcc.Graph(id='bike-map'),

#     # Graph for private vehicle usage by hour
#     dcc.Graph(id='private-vehicle-usage'),
# ])

# # Callbacks for interactive graphs

# # Peak public transport usage graph
# @app.callback(
#     Output('main-graph', 'figure'),
#     [Input('data-selector', 'value')]
# )
# def update_main_graph(selected_data):
#     if selected_data == 'transport':
#         fig = px.bar(peak_transport_usage, x='Peak Period', y='Passenger Count',
#                      title='Public Transport Usage During Peak Periods')
#         return fig
#     elif selected_data == 'vehicle':
#         fig = px.bar(vehicle_registration_df, x='POSTCODE', y='Estimated Emissions',
#                      title='Estimated Carbon Emissions by Postcode')
#         return fig

# # Pie chart for emissions by fuel type
# @app.callback(
#     Output('emission-pie-chart', 'figure'),
#     [Input('data-selector', 'value')]
# )
# def update_emission_pie_chart(selected_data):
#     if selected_data == 'vehicle':
#         emissions_by_fuel = vehicle_registration_df.groupby('CD_CL_FUEL_ENG')['Estimated Emissions'].sum()
#         fig = px.pie(values=emissions_by_fuel, names=emissions_by_fuel.index,
#                      title='Proportion of Emissions by Fuel Type')
#         return fig

# Correlation heatmap for vehicle registration data
# @app.callback(
#     Output('correlation-heatmap', 'figure'),
#     [Input('data-selector', 'value')]
# )
# def update_correlation_heatmap(selected_data):
#     if selected_data == 'vehicle':
#         corr_matrix = vehicle_registration_df.corr()
#         fig = ff.create_annotated_heatmap(z=corr_matrix.values,
#                                           x=list(corr_matrix.columns),
#                                           y=list(corr_matrix.index),
#                                           colorscale='Viridis')
#         return fig

# # Geospatial map for biking infrastructure
# @app.callback(
#     Output('bike-map', 'figure'),
#     [Input('data-selector', 'value')]
# )
# def update_bike_map(selected_data):
#     if selected_data == 'bike':
#         gdf = gpd.GeoDataFrame(bicycle_network_df, geometry=gpd.points_from_xy(bicycle_network_df['Longitude'], bicycle_network_df['Latitude']))
#         fig = px.scatter_mapbox(gdf, lat='Latitude', lon='Longitude', size='Length',
#                                 title='Biking Infrastructure', zoom=10,
#                                 mapbox_style="open-street-map")
#         return fig

# # Private vehicle commute usage graph
# @app.callback(
#     Output('private-vehicle-usage', 'figure'),
#     [Input('data-selector', 'value')]
# )
# def update_private_vehicle_usage(selected_data):
#     if selected_data == 'private_vehicle':
#         private_vehicle_commuters = journey_to_work_df[journey_to_work_df['jtwmode'] == 'Private Vehicle']
#         private_vehicle_usage_by_hour = private_vehicle_commuters.groupby('starthour')['jtwtraveltime'].count().reset_index()
#         private_vehicle_usage_by_hour.columns = ['Start Hour', 'Number of Private Vehicle Users']
#         fig = px.bar(private_vehicle_usage_by_hour, x='Start Hour', y='Number of Private Vehicle Users',
#                      title='Private Vehicle Usage During Commutes by Hour')
#         return fig

# Run the Dash app
# if __name__ == '__main__':
#     app.run_server(debug=True)
