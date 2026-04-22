import numpy as np
import matplotlib.pyplot as plt
from itertools import product

from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

import load

data = load.load_file()
start_coords_DF = load.get_start_station_coords(data)
dest_coords_DF = load.get_dest_station_coords(data)


def _build_start_station_stats():
    station_counts = data.value_counts(subset="start.station.id").reset_index(name="trip_count")
    station_meta = data.drop_duplicates(subset=["start.station.id"])[[
        "start.station.id",
        "start.station.name",
        "start.station.latitude",
        "start.station.longitude"
    ]]
    stats = station_meta.merge(station_counts, on="start.station.id", how="inner")
    rank = stats["trip_count"].rank(method="first")
    stats["traffic_tier"] = np.ceil(rank / len(stats) * 3).astype(int).clip(1, 3)
    stats["availability"] = stats["traffic_tier"].map({1: "High", 2: "Medium", 3: "Low"})
    return stats


def _build_end_station_stats():
    station_counts = data.value_counts(subset="end.station.id").reset_index(name="trip_count")
    station_meta = data.drop_duplicates(subset=["end.station.id"])[[
        "end.station.id",
        "end.station.name",
        "end.station.latitude",
        "end.station.longitude"
    ]]
    stats = station_meta.merge(station_counts, on="end.station.id", how="inner")
    rank = stats["trip_count"].rank(method="first")
    stats["traffic_tier"] = np.ceil(rank / len(stats) * 3).astype(int).clip(1, 3)
    stats["availability"] = stats["traffic_tier"].map({1: "High", 2: "Medium", 3: "Low"})
    return stats


START_STATION_STATS = _build_start_station_stats()
END_STATION_STATS = _build_end_station_stats()


def _haversine_miles(lat1, lon1, lat2, lon2):
    earth_radius_miles = 3958.7613
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = np.radians([lat1, lon1, lat2, lon2])
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return earth_radius_miles * c


def get_top_route_candidates(start_point, end_point, top_n=5, start_candidates=8, end_candidates=8):
    start_lat, start_lng = start_point
    end_lat, end_lng = end_point

    start_df = START_STATION_STATS.copy()
    end_df = END_STATION_STATS.copy()

    start_df["distance_to_start_miles"] = start_df.apply(
        lambda row: _haversine_miles(start_lat, start_lng, row["start.station.latitude"], row["start.station.longitude"]),
        axis=1
    )
    end_df["distance_from_end_miles"] = end_df.apply(
        lambda row: _haversine_miles(end_lat, end_lng, row["end.station.latitude"], row["end.station.longitude"]),
        axis=1
    )

    top_start_df = start_df.nsmallest(start_candidates, "distance_to_start_miles")
    top_end_df = end_df.nsmallest(end_candidates, "distance_from_end_miles")

    routes = []
    for start_row, end_row in product(top_start_df.to_dict("records"), top_end_df.to_dict("records")):
        route_distance_miles = _haversine_miles(
            start_row["start.station.latitude"],
            start_row["start.station.longitude"],
            end_row["end.station.latitude"],
            end_row["end.station.longitude"]
        )

        availability_penalty = (start_row["traffic_tier"] + end_row["traffic_tier"]) * 0.15
        score = (
            start_row["distance_to_start_miles"]
            + route_distance_miles
            + end_row["distance_from_end_miles"]
            + availability_penalty
        )

        routes.append({
            "start_station_name": start_row["start.station.name"],
            "end_station_name": end_row["end.station.name"],
            "distance_to_start_station_miles": round(start_row["distance_to_start_miles"], 3),
            "route_distance_miles": round(route_distance_miles, 3),
            "distance_from_end_station_miles": round(end_row["distance_from_end_miles"], 3),
            "total_access_distance_miles": round(
                start_row["distance_to_start_miles"] + route_distance_miles + end_row["distance_from_end_miles"],
                3
            ),
            "start_station_availability": start_row["availability"],
            "end_station_availability": end_row["availability"],
            "start_station_trip_count": int(start_row["trip_count"]),
            "end_station_trip_count": int(end_row["trip_count"]),
            "score": round(score, 3)
        })

    routes.sort(key=lambda x: x["score"])
    return routes[:top_n]


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
print_clusters()
