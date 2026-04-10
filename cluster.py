import numpy as np
import matplotlib.pyplot as plt

from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

import load

data = load.load_file()
start_coords_DF = load.get_start_station_coords(data)
dest_coords_DF = load.get_dest_station_coords(data)


# Finds the nearest starting clusters from a location.
# params: latitude, longitude, n amount of clusters to be returned
# return: n lists of station coordinates as tuples in each cluster
def get_nearest_start_clusters(lat, long, n):
    station_counts = data.value_counts(subset="start.station.id").reset_index(name="trip_count")
    station_coords_DF = start_coords_DF.merge(station_counts, on="start.station.id")

    # clustering based on traffic (trip_count)
    clust_feats = station_coords_DF.filter(items=("trip_count",))
    scaler = StandardScaler()
    scaled_feats = scaler.fit_transform(clust_feats)
    kmeans = KMeans(n_clusters=3, random_state=0, n_init="auto")
    station_coords_DF["traffic_cluster"] = kmeans.fit_predict(scaled_feats)

    # calculate the average location (center) for each cluster
    cluster_centers = station_coords_DF.groupby("traffic_cluster")[["start.station.latitude", "start.station.longitude"]].mean()

    # calculate distance from input (lat, long) to each cluster center
    input_coords = [[lat, long]]
    distances = cdist(input_coords, cluster_centers.values, metric='euclidean')[0]

    # get the indices of the 'n' closest clusters
    nearest_cluster_ids = distances.argsort()[:n]

    # build the list of lists containing coordinate tuples
    results = []
    for cluster_id in nearest_cluster_ids:
        cluster_stations = station_coords_DF[station_coords_DF["traffic_cluster"] == cluster_id]
        # create list of tuples: [(lat1, lon1), (lat2, lon2), ...]
        coords_list = list(zip(cluster_stations["start.station.latitude"], cluster_stations["start.station.longitude"]))
        results.append(coords_list)

    return results


# Finds the nearest destination clusters from a location.
# params: latitude, longitude, n amount of clusters to be returned
# return: n lists of station coordinates as tuples in each cluster
def get_nearest_dest_clusters(lat, long, n):
    station_counts = data.value_counts(subset="end.station.id").reset_index(name="trip_count")
    station_coords_DF = dest_coords_DF.merge(station_counts, on="end.station.id")

    # clustering based on traffic (trip_count)
    clust_feats = station_coords_DF.filter(items=("trip_count",))
    scaler = StandardScaler()
    scaled_feats = scaler.fit_transform(clust_feats)
    kmeans = KMeans(n_clusters=3, random_state=0, n_init="auto")
    station_coords_DF["traffic_cluster"] = kmeans.fit_predict(scaled_feats)

    # calculate the average location (center) for each cluster
    cluster_centers = station_coords_DF.groupby("traffic_cluster")[["end.station.latitude", "end.station.longitude"]].mean()

    # calculate distance from input (lat, long) to each cluster center
    input_coords = [[lat, long]]
    distances = cdist(input_coords, cluster_centers.values, metric='euclidean')[0]

    # get the indices of the 'n' closest clusters
    nearest_cluster_ids = distances.argsort()[:n]

    # build the list of lists containing coordinate tuples
    results = []
    for cluster_id in nearest_cluster_ids:
        cluster_stations = station_coords_DF[station_coords_DF["traffic_cluster"] == cluster_id]
        # create list of tuples: [(lat1, lon1), (lat2, lon2), ...]
        coords_list = list(zip(cluster_stations["end.station.latitude"], cluster_stations["end.station.longitude"]))
        results.append(coords_list)

    return results


# Uses matplotlib to construct a figure of starting station clusters
def print_clusters():
    stationCounts = data.value_counts(subset="start.station.id").reset_index(name="trip_count")
    stationCoordsDF = start_coords_DF.merge(stationCounts, on="start.station.id")
    clustFeats = stationCoordsDF.filter(items=("trip_count",))
    scaler = StandardScaler()
    scaledFeats = scaler.fit_transform(clustFeats)
    kmeans = KMeans(n_clusters=3, random_state=0)
    stationCoordsDF["traffic_cluster"] = kmeans.fit_predict(scaledFeats)

    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(
        stationCoordsDF["start.station.longitude"],
        stationCoordsDF["start.station.latitude"],
        c=stationCoordsDF["traffic_cluster"],
        s=(stationCoordsDF["trip_count"] / 5),
        alpha=0.75)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Station Traffic")
    xMin = stationCoordsDF["start.station.longitude"].min()
    xMax = stationCoordsDF["start.station.longitude"].max()
    yMin = stationCoordsDF["start.station.latitude"].min()
    yMax = stationCoordsDF["start.station.latitude"].max()
    xSpace = np.linspace(xMin, xMax, num=7)
    ySpace = np.linspace(yMin, yMax, num=10)
    ax.set_xticks(xSpace)
    ax.set_yticks(ySpace)

    handles, labels = scatter.legend_elements()
    clusterMeans = stationCoordsDF.groupby("traffic_cluster").trip_count.mean()
    sortedClusters = clusterMeans.sort_values(ascending=False).index

    sortedHandlesList = []
    for i in sortedClusters:
        sortedHandlesList.append(handles[i])

    sortedHandles = tuple(sortedHandlesList)
    sortedLabels = ("High Traffic", "Medium Traffic", "Low Traffic")
    legend = ax.legend(sortedHandles, sortedLabels, title="Traffic Tier")

    plt.show()

# REMOVE COMMENT BELOW TO SHOW CLUSTER FIGURE
#print_clusters()
