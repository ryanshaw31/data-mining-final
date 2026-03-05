import numpy as np
import pandas as pd
import collections as col

def matchNameToID(data):
    pd.set_option("display.max_columns", None) # allows all columns to be viewed
    station_ids = data['start.station.id'].unique().tolist()
    sorted_station_ids = sorted(station_ids)
    start_station_names = data['start.station.name'].unique().tolist()

    stations = dict(zip(sorted_station_ids, start_station_names))
    
    return stations

def createStartEndList(data):
    '''Returns a triple tuple list of how often each start and end location combination occurs in the dataset'''

    start_station_names = data['start.station.name'].tolist()
    end_station_names = data['end.station.name'].tolist()
    tripStartEnd = list(zip(start_station_names, end_station_names))
    tripCounter = col.Counter(tripStartEnd)

    return tripCounter



