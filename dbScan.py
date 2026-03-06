import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
df = pd.read_csv("bike_data.csv")

#coordinates only
coords = df[['start.station.latitude', 'start.station.longitude']].dropna()

X = coords.to_numpy()

#degrees to radians
X_rad = np.radians(X)


earth_radius = 6371.0088

#kilometers converted to radians
eps_km = 0.5  #500 meters
eps = eps_km / earth_radius

db = DBSCAN(
    eps=eps,
    min_samples=10,
    metric='haversine'
)

labels = db.fit_predict(X_rad)

coords['cluster'] = labels

import matplotlib.pyplot as plt

plt.figure(figsize=(8,8))
plt.scatter(
    coords['start.station.latitude'],
    coords['start.station.longitude'],
    c=coords['cluster'],
    cmap='tab20',
    s=5
)
plt.title("DBSCAN Clusters of Citi Bike Start Locations")
plt.show()