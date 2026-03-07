import pandas as pd


def load_file():
    data = pd.read_csv('bike_data.csv')
    return data

def match_name_to_id(data):
    unique_stations = data.drop_duplicates(subset = ["start.station.id"])
    stations = unique_stations.set_index("start.station.id")["start.station.name"].to_dict()
    stations_sorted = dict(sorted(stations.items()))
    return stations_sorted

def create_start_end_list(data):
    trip_counts = data[['start.station.name', 'end.station.name']].value_counts()
    return trip_counts.to_dict()

def get_station_coordinates(data):
    unique_stations = data.drop_duplicates(subset = ["start.station.id"])
    coords = unique_stations[["start.station.id", "start.station.latitude", "start.station.longitude"]].copy()
    coords_sorted = coords.sort_values(by="start.station.id")
    return coords_sorted
