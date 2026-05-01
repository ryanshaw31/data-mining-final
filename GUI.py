import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

import requests
import csv
import os

from dotenv import load_dotenv

import cluster
import AIStuff


# ----------------- Load API key -----------------

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
WIDTH = 600
HEIGHT = 600


# ----------------- Compute map center -----------------

latitudes = [s["lat"] for s in stations]
longitudes = [s["lng"] for s in stations]

CENTER_LAT = sum(latitudes) / len(latitudes)
CENTER_LNG = sum(longitudes) / len(longitudes)


# ----------------- Approximate map bounds -----------------

scale = 360 / (2 ** (ZOOM + 8))

LAT_TOP = CENTER_LAT + (HEIGHT / 2) * scale
LAT_BOTTOM = CENTER_LAT - (HEIGHT / 2) * scale
LNG_LEFT = CENTER_LNG - (WIDTH / 2) * scale
LNG_RIGHT = CENTER_LNG + (WIDTH / 2) * scale


# ----------------- Coordinate conversion -----------------

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
        url = (
            f"https://maps.googleapis.com/maps/api/staticmap?"
            f"center={CENTER_LAT},{CENTER_LNG}&"
            f"zoom={ZOOM}&"
            f"size={WIDTH}x{HEIGHT}&"
            f"key={API_KEY}"
        )

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


# ----------------- Route Viewer -----------------

class RouteViewer:

    def __init__(
        self,
        root,
        map_image,
        routes,
        ai_text,
        user_start,
        user_end
    ):

        self.routes = routes
        self.ai_text = ai_text
        self.user_start = user_start
        self.user_end = user_end

        self.index = 0

        self.window = tk.Toplevel(root)
        self.window.title("Citi Bike Route Viewer")

        self.canvas = tk.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )

        self.canvas.pack()

        self.photo = ImageTk.PhotoImage(map_image)

        self.canvas.create_image(
            0,
            0,
            anchor=tk.NW,
            image=self.photo
        )

        self.info_label = tk.Label(
            self.window,
            text="",
            justify="left",
            font=("Arial", 11)
        )

        self.info_label.pack(pady=8)

        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)

        prev_button = tk.Button(
            button_frame,
            text="Previous Route",
            command=self.prev_route,
            width=15
        )

        prev_button.pack(side=tk.LEFT, padx=10)

        next_button = tk.Button(
            button_frame,
            text="Next Route",
            command=self.next_route,
            width=15
        )

        next_button.pack(side=tk.LEFT, padx=10)

        self.draw_route()


    def draw_route(self):

        self.canvas.delete("overlay")

        route = self.routes[self.index]

        start_station = (
            route["start_station_lat"],
            route["start_station_lng"]
        )

        end_station = (
            route["end_station_lat"],
            route["end_station_lng"]
        )

        user_start_x, user_start_y = latlng_to_pixel(*self.user_start)

        start_x, start_y = latlng_to_pixel(*start_station)

        end_x, end_y = latlng_to_pixel(*end_station)

        user_end_x, user_end_y = latlng_to_pixel(*self.user_end)

        radius = 7


        # User start

        self.canvas.create_oval(
            user_start_x - radius,
            user_start_y - radius,
            user_start_x + radius,
            user_start_y + radius,
            fill="red",
            outline="black",
            width=2,
            tags="overlay"
        )


        # User destination

        self.canvas.create_oval(
            user_end_x - radius,
            user_end_y - radius,
            user_end_x + radius,
            user_end_y + radius,
            fill="green",
            outline="black",
            width=2,
            tags="overlay"
        )


        # Start station

        self.canvas.create_oval(
            start_x - radius,
            start_y - radius,
            start_x + radius,
            start_y + radius,
            fill="orange",
            outline="black",
            width=2,
            tags="overlay"
        )


        # End station

        self.canvas.create_oval(
            end_x - radius,
            end_y - radius,
            end_x + radius,
            end_y + radius,
            fill="purple",
            outline="black",
            width=2,
            tags="overlay"
        )


        # Walk to start station

        self.canvas.create_line(
            user_start_x,
            user_start_y,
            start_x,
            start_y,
            fill="gray",
            width=2,
            dash=(4, 2),
            tags="overlay"
        )


        # Main bike route

        self.canvas.create_line(
            start_x,
            start_y,
            end_x,
            end_y,
            fill="blue",
            width=5,
            tags="overlay"
        )


        # Walk to destination

        self.canvas.create_line(
            end_x,
            end_y,
            user_end_x,
            user_end_y,
            fill="gray",
            width=2,
            dash=(4, 2),
            tags="overlay"
        )


        info = (
            f"Route #{self.index + 1}\n\n"
            f"Start Station: {route['start_station_name']}\n"
            f"End Station: {route['end_station_name']}\n\n"
            f"Walk To Start: {route['distance_to_start_station_miles']} miles\n"
            f"Bike Route: {route['route_distance_miles']} miles\n"
            f"Walk To Destination: {route['distance_from_end_station_miles']} miles\n\n"
            f"Start Availability: {route['start_station_availability']}\n"
            f"End Availability: {route['end_station_availability']}"
        )

        self.info_label.config(text=info)


    def next_route(self):

        self.index = (self.index + 1) % len(self.routes)
        self.draw_route()


    def prev_route(self):

        self.index = (self.index - 1) % len(self.routes)
        self.draw_route()


# ----------------- GUI -----------------

root = tk.Tk()
root.title("Citi Bike Map Viewer")

img = Image.open(map_file)
photo = ImageTk.PhotoImage(img)

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT)
canvas.pack()

canvas.create_image(
    0,
    0,
    anchor=tk.NW,
    image=photo
)

clicked_points = []
dot_ids = []


# ----------------- Draw stations -----------------

for s in stations:

    x, y = latlng_to_pixel(s["lat"], s["lng"])

    radius = 5

    canvas.create_oval(
        x - radius,
        y - radius,
        x + radius,
        y + radius,
        fill="yellow",
        outline="black",
        width=2
    )


# ----------------- Click handling -----------------

def on_click(event):

    lat, lng = pixel_to_latlng(event.x, event.y)

    color = "red" if len(clicked_points) % 2 == 0 else "green"

    clicked_points.append((lat, lng))

    print(f"Clicked lat/lng: {lat}, {lng} (color={color})")


    radius = 6

    dot_id = canvas.create_oval(
        event.x - radius,
        event.y - radius,
        event.x + radius,
        event.y + radius,
        fill=color,
        outline="black",
        width=2
    )

    dot_ids.append(dot_id)


    if color == "red":

        closest_start_clusters = cluster.get_nearest_start_clusters(
            lat,
            lng,
            2
        )

        print("Nearest start clusters:")
        print(closest_start_clusters)


    elif color == "green":

        closest_end_clusters = cluster.get_nearest_dest_clusters(
            lat,
            lng,
            2
        )

        print("Nearest destination clusters:")
        print(closest_end_clusters)


        start_point = clicked_points[-2]
        end_point = clicked_points[-1]


        try:

            routes, recommendation_text = AIStuff.generate_recommendation(
                start_point,
                end_point,
                top_n=5
            )

            print("\nTop 5 route recommendations:\n")
            print(recommendation_text)


            RouteViewer(
                root,
                img,
                routes,
                recommendation_text,
                start_point,
                end_point
            )


        except Exception as exc:

            print(f"Failed to generate recommendation: {exc}")

            messagebox.showerror(
                "Recommendation Error",
                str(exc)
            )


canvas.bind("<Button-1>", on_click)


# ----------------- Clear button -----------------

def clear_clicks():

    clicked_points.clear()

    for dot_id in dot_ids:
        canvas.delete(dot_id)

    dot_ids.clear()

    print("Cleared all clicked points.")


clear_button = tk.Button(
    root,
    text="Clear Clicks",
    command=clear_clicks
)

clear_button.pack(pady=10)


root.mainloop()
