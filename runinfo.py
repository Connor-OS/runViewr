import numpy as np
import pandas as pd
from gpx_converter import Converter
from os import listdir
import datetime
import requests
from time import sleep
import plotly.express as px

class RunInfo:
    def __init__(self,file):
        #initalise data stream from file
        self.stream = Converter(input_file=f'./GPS-data/{file}').gpx_to_dataframe()
        
        #initalise basic info
        stream_len = len(self.stream['time'])
        self.duration = self.stream['time'][stream_len-1] - self.stream['time'][0]
        self.date = self.stream['time'][0].date()

        #simplify time
        self.stream['time'] = self.stream['time'].apply(lambda x: x.time())
        self.stream.columns = ['time','lat','lon','alt']

        self.dist = 0
        #compute extra info
        R = 6373.0
        x, y = np.deg2rad(self.stream['lon']), np.deg2rad(self.stream['lat'])
        for i in range(stream_len-1):
            dlon = x[i]-x[i+1]
            dlat = y[i]-y[i+1]
            a = np.sin(dlat / 2)**2 + np.cos(y[i]) * np.cos(y[i+1]) * np.sin(dlon / 2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
            self.dist += R*c


        
        self.cent = [self.stream['lon'].sum()/len(self.stream),self.stream['lat'].sum()/len(self.stream)]

        #potentially add more data such as 5 and 10k times
        # self._5k = 
        # self._10k =


class RunInfo_strava:
    def __init__(self,activity,access_token):
        self.id = activity['id']
        self.duration = activity['moving_time']
        self.date = datetime.date.fromisoformat(activity['start_date'][:10])
        self.dist = activity['distance']/1000
        r = requests.get(f"https://www.strava.com/api/v3/activities/{activity['id']}/streams?keys=latlng&key_by_type=true", headers={"Authorization":f"Bearer {access_token}"}).json()
        try:
            self.stream = pd.DataFrame(r['latlng']['data'],columns=['lat','lon'])
            self.cent = [self.stream['lon'].sum()/len(self.stream),self.stream['lat'].sum()/len(self.stream)]
        except:
            self.stream = []