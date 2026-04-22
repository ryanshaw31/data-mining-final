import tkinter as tk
from PIL import Image, ImageTk
import requests
import csv
import os
from dotenv import load_dotenv
from tkinter import messagebox

import cluster
import AIStuff

# ----------------- Load API key -----------------
# Support either .env or APIKey.env in the project root.
load_dotenv(".env")
load_dotenv("APIKey.env")
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY not found in .env or APIKey.env")

# ----------------- Load bike stations from CSV -----------------
stations = []
with open("bike_data.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        stations.append({
            "name": row["start.station.name"],
            "lat": float(row["start.station.latitude"]),
            "lng": float(row["start.station.longitude"])
        })

# ----------------- Map configuration -----------------
ZOOM = 14
WIDTH, HEIGHT = 600, 600

# ----------------- Compute dynamic center -----------------
latitudes = [s["lat"] for s in stations]
longitudes = [s["lng"] for s in stations]

CENTER_LAT = sum(latitudes) / len(latitudes)
CENTER_LNG = sum(longitudes) / len(longitudes)

# ----------------- Approximate bounds based on zoom -----------------
# degrees per pixel approximation
scale = 360 / (2 ** (ZOOM + 8))

LAT_TOP = CENTER_LAT + (HEIGHT / 2) * scale
LAT_BOTTOM = CENTER_LAT - (HEIGHT / 2) * scale
LNG_LEFT = CENTER_LNG - (WIDTH / 2) * scale
LNG_RIGHT = CENTER_LNG + (WIDTH / 2) * scale


def pixel_to_latlng(x_pixel, y_pixel):
    lat = LAT_TOP - (y_pixel / HEIGHT) * (LAT_TOP - LAT_BOTTOM)
    lng = LNG_LEFT + (x_pixel / WIDTH) * (LNG_RIGHT - LNG_LEFT)
    return lat, lng


def latlng_to_pixel(lat, lng):
    x = int((lng - LNG_LEFT) / (LNG_RIGHT - LNG_LEFT) * WIDTH)
    y = int((LAT_TOP - lat) / (LAT_TOP - LAT_BOTTOM) * HEIGHT)
    return x, y


# ----------------- Fetch map -----------------
map_file = "map.png"
if not os.path.exists(map_file):
    try:
        url = f"https://maps.googleapis.com/maps/api/staticmap?center={CENTER_LAT},{CENTER_LNG}&zoom={ZOOM}&size={WIDTH}x{HEIGHT}&key={API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(map_file, "wb") as f:
            f.write(response.content)
        print("Map fetched and saved locally.")
    except requests.exceptions.RequestException as e:
        print("Failed to fetch map:", e)
        exit(1)
else:
    print("Using cached map.")

# ----------------- GUI -----------------
root = tk.Tk()
root.title("Citi Bike Map Viewer")

img = Image.open(map_file)
photo = ImageTk.PhotoImage(img)

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT)
canvas.pack()
canvas_img = canvas.create_image(0, 0, anchor=tk.NW, image=photo)

clicked_points = []
dot_ids = []

# ----------------- Draw all stations -----------------
for s in stations:
    x, y = latlng_to_pixel(s["lat"], s["lng"])
    radius = 5
    canvas.create_oval(
        x - radius, y - radius, x + radius, y + radius,
        fill="yellow", outline="black", width=2
    )


# ----------------- Handle clicks -----------------
def on_click(event):
    lat, lng = pixel_to_latlng(event.x, event.y)

    # First click = red (start), second = green (destination)
    color = "red" if len(clicked_points) % 2 == 0 else "green"

    clicked_points.append((lat, lng))
    print(f"Clicked lat/lng: {lat}, {lng} (color={color})")

    # Finds closest clusters to location
    cluster_amount = 2
    if color == "red":
        closest_start_clusters = cluster.get_nearest_start_clusters(lat, lng, cluster_amount)
        print(closest_start_clusters)
    elif color == "green":
        closest_end_clusters = cluster.get_nearest_dest_clusters(lat, lng, cluster_amount)
        print(closest_end_clusters)
        start_point = clicked_points[-2]
        end_point = clicked_points[-1]
        try:
            recommendation = AIStuff.generate_recommendation(start_point, end_point, top_n=5)
            print("\nTop 5 route recommendations:\n")
            print(recommendation)
            messagebox.showinfo("Top 5 Route Recommendations", recommendation)
        except Exception as exc:
            print(f"Failed to generate AI recommendation: {exc}")


    radius = 6
    dot_id = canvas.create_oval(
        event.x - radius, event.y - radius,
        event.x + radius, event.y + radius,
        fill=color, outline="black", width=2
    )
    dot_ids.append(dot_id)


canvas.bind("<Button-1>", on_click)


# ----------------- Clear clicks button -----------------
def clear_clicks():
    clicked_points.clear()
    for dot_id in dot_ids:
        canvas.delete(dot_id)
    dot_ids.clear()
    print("Cleared all clicked points.")


clear_button = tk.Button(root, text="Clear Clicks", command=clear_clicks)
clear_button.pack(pady=10)


root.mainloop()