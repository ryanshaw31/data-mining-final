import load

import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN


data = load.load_file()

#coordinates only
coords = data[['start.station.latitude', 'start.station.longitude']].dropna()
X = coords.to_numpy()
X_rad = np.radians(X) #degrees to radians

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
