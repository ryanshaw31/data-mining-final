
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np
import load

def kMeans(file_path):
    data = pd.read_csv(file_path)
    coordsDF = load.getStationCoordinates(data)

    stationCounts = data.value_counts(subset = "start.station.id").reset_index(name = "trip_count")
    stationCoordsDF = coordsDF.merge(stationCounts, on = "start.station.id")
    clustFeats = stationCoordsDF.filter(items = ("trip_count",))
    scaler = StandardScaler()
    scaledFeats = scaler.fit_transform(clustFeats)
    kmeans = KMeans(n_clusters = 3, random_state = 0)
    stationCoordsDF["traffic_cluster"] = kmeans.fit_predict(scaledFeats)
    fig, ax = plt.subplots(figsize = (10, 8))
    scatter = ax.scatter(stationCoordsDF["start.station.longitude"], stationCoordsDF["start.station.latitude"], c = stationCoordsDF["traffic_cluster"], s = (stationCoordsDF["trip_count"] / 5), alpha = 0.75)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Station Traffic")
    xMin = stationCoordsDF["start.station.longitude"].min()
    xMax = stationCoordsDF["start.station.longitude"].max()
    yMin = stationCoordsDF["start.station.latitude"].min()
    yMax = stationCoordsDF["start.station.latitude"].max()
    xSpace = np.linspace(xMin, xMax, num = 7)
    ySpace = np.linspace(yMin, yMax, num = 10)
    ax.set_xticks(xSpace)
    ax.set_yticks(ySpace)

    handles, labels = scatter.legend_elements()
    clusterMeans = stationCoordsDF.groupby("traffic_cluster").trip_count.mean()
    sortedClusters = clusterMeans.sort_values(ascending = False).index

    sortedHandlesList = []
    for i in sortedClusters:
        sortedHandlesList.append(handles[i])

    sortedHandles = tuple(sortedHandlesList)
    sortedLabels = ("High Traffic", "Medium Traffic", "Low Traffic")
    legend = ax.legend(sortedHandles, sortedLabels, title = "Traffic Tier")

    plt.show()

kMeans("bike_data.csv")