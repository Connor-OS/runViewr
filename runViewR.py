import plotly.express as px
import numpy as np
import pandas as pd
from gpx_converter import Converter
from os import listdir
import datetime
import requests
from time import sleep
from runinfo import RunInfo, RunInfo_strava

from oauthlib.oauth2 import WebApplicationClient
import dash
from dash import dcc, html, Input, Output  

app = dash.Dash(__name__)

#-----------------------------------
#Import and format user data
#Use pre loaded GPS-data or make a call to the users Strava

CLIENT_ID = 95789 #bad form to have a client ID out in the open like this 

center_index = 0

auth_url = "http://www.strava.com/oauth/authorize?client_id=95789&response_type=code&redirect_uri=http://127.0.0.1:8050/&approval_prompt=force&scope=activity:read"
colour_scheme = px.colors.qualitative.Prism[:9]

#Preloaded GRN data
gpx_files = listdir('./GPS-data')
gpx_files.sort()
run_data = []
for file in gpx_files:
    run_data.append(RunInfo(file))

#----------------------------------
#App Layout

app.layout = html.Div([

    html.H1("RunViewR, simple web based run visualiser", style={'text-align': 'center'}),

    dcc.DatePickerRange(
        id='date_range',
        start_date_placeholder_text='Start date',
        end_date_placeholder_text='End date',
        display_format='DD MM YYYY',
    ),

    html.Button(id='center_run', children='See next runs', n_clicks=0),

    html.Div(
        [dcc.Loading(id="loading-1", type="default", children=html.P(id='placeholder',hidden=True)),
        html.A(id='strava_auth_link', href=auth_url, children='Use your own strava data', n_clicks=0),]
    ),

    html.Div(id='summary_stats'),

    html.Div(children=[
        dcc.Graph(id='run_map', figure={},style={'width': '90vh', 'height': '90vh'})],
        style={'display': 'inline-block'}),

    html.Div(children=[
        dcc.Graph(id='hist', figure={},style={'width': '90vh', 'height': '90vh'}),],
        style={'display': 'inline-block'}),

    html.Div(children=[
        "welcome to runViewer, a simple but powerfull runviewing data dashboard,"],
        style={'display': 'inline-block'}),




    dcc.Location(id='url'),
])


#-------------------------------
#callback for strava authentification
@app.callback(
    Output('placeholder', 'hidden'),
    Input('url', 'href'))

def authorize_strava(href):

    if 'code' not in href: return True
    authorization_code = href.split('code=')[1].split('&')[0].strip()
    try:
        refresh_token = requests.post(f'https://www.strava.com/oauth/token\
?client_id=95789\
&client_secret=927c7cb23e544d34b5349515b8b42b0ea5e0d4b5\
&code={authorization_code}\
&grant_type=authorization_code').json()['refresh_token']
    except: return True

    access_token = requests.post(f'https://www.strava.com/oauth/token\
?client_id=95789\
&client_secret=927c7cb23e544d34b5349515b8b42b0ea5e0d4b5\
&refresh_token={refresh_token}\
&grant_type=refresh_token').json()['access_token']

    activities = requests.get(f"https://www.strava.com/api/v3/athlete/activities?\
access_token={access_token}").json()
    run_data.clear()
    c = 0
    for activity in activities:
        c += 1
        print(c)
        run_data.append(RunInfo_strava(activity,access_token))
    return True


#-------------------------------
#callback for data selection
@app.callback(
    [Output('run_map','figure'),
    Output('hist','figure'),
    Output('summary_stats','children')],
    [Input('date_range','start_date'),
    Input('date_range','end_date'),
    Input('center_run','n_clicks'),
    Input('placeholder','hidden')]
)

def choose_data(start_date,end_date,n_clicks,hidden):
    # Apply date filtering
    if type(start_date) == str :
        start_date = datetime.date.fromisoformat(start_date)
    else:
        start_date = datetime.date(1900,1,1)

    if type(end_date) == str :
        end_date = datetime.date.fromisoformat(end_date)
    else:
        end_date = datetime.date.today()

    run_data_filtered = []
    for run in run_data:
        if run.date > start_date and run.date < end_date:
            run_data_filtered.append(run)
    print(len(run_data_filtered))

    #compute graph args
    lat = []
    lon = []
    # time = []
    date = []
    summary_data = []

    for run in run_data_filtered:
        # time = time + list(run.stream['time'])
        lat = lat + list(run.stream['lat'])
        lon = lon + list(run.stream['lon'])
        date = date + [run.date]*len(run.stream)
        summary_data.append([run.date,run.date.strftime('%b %y'),run.dist,run.duration])

    rundf = pd.DataFrame(list(zip(lat, lon, date)),
                    columns=['lat', 'lon', 'Date'])
    summarydf = pd.DataFrame(summary_data,columns=['Date','month','dist','duration'])

    summary_stats = f'Displaying {len(run_data_filtered)} runs'

    #cycle run center
    if len(run_data_filtered) != 0:
        center_index = n_clicks%len(run_data_filtered)
        center={'lon': run_data_filtered[center_index].cent[0], 'lat': run_data_filtered[center_index].cent[1]}
    else:
        summary_stats = 'No runs displayed'
        center = {'lon': 0.0, 'lat': 0.0}

    #use mapbox token
    px.set_mapbox_access_token(open(".mapbox_token").read())

    #The plotly graph map
    fig1 = px.line_mapbox(rundf,
                    lat='lat', 
                    lon='lon', 
                    # hover_name='Date',
                    hover_data={
                        # "lats": ":.2f",
                        # "lons": ":.2f",
                        # "times": ":%I:%M %p"
                    },
                    title = 'Run view',
                    color='Date',
                    color_discrete_sequence=colour_scheme,
                    center = center,
                    zoom=11)

    # fig2 = px.histogram(summarydf, x="date", y='dist',nbins=12,title='Kilometers run histogram',labels={'dist':'distance (km)','date':'Date'})
    fig2 = px.bar(summarydf, 
                    x="month", 
                    y='dist',
                    title='Run distance',
                    labels={'dist':'Distance (km)'},
                    color='Date',
                    color_discrete_sequence=colour_scheme)

    return fig1,fig2,summary_stats


# ------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)