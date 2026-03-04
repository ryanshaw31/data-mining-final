import pandas as pd

data = pd.read_csv('bike_data.csv')
pd.set_option("display.max_columns", None) # allows all columns to be viewed

station_ids = data['start.station.id'].unique().tolist()
sorted_station_ids = sorted(station_ids)
station_names = data['start.station.name'].unique().tolist()

stations = dict(zip(sorted_station_ids, station_names))
