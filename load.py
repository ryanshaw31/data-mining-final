import pandas as pd

def matchNameToID(data):
    pd.set_option("display.max_columns", None)
    uniqueStations = data.drop_duplicates(subset = ["start.station.id"])
    stations = uniqueStations.set_index("start.station.id")["start.station.name"].to_dict()

    return stations

def createStartEndList(data):
    tripCounts = data[['start.station.name', 'end.station.name']].value_counts()

    return tripCounts.to_dict()

def getStationCoordinates(data):
    uniqueStations = data.drop_duplicates(subset = ["start.station.id"])
    coords = uniqueStations[["start.station.id", "start.station.latitude", "start.station.longitude"]].copy()

    return coords