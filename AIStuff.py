from openai import OpenAI

import os

from dotenv import load_dotenv

import cluster


# ----------------- Load environment -----------------

load_dotenv(".env")
load_dotenv("APIKey.env")


# ----------------- OpenAI client -----------------

client = OpenAI()


# ----------------- Recommendation generation -----------------

def generate_recommendation(start_point, end_point, top_n=5):

    candidate_routes = cluster.get_top_route_candidates(
        start_point,
        end_point,
        top_n=top_n
    )


    formatted_candidates = "\n".join(
        [
            (
                f"{idx}. "
                f"Start: {route['start_station_name']} | "
                f"End: {route['end_station_name']} | "
                f"to_start_miles={route['distance_to_start_station_miles']} | "
                f"route_miles={route['route_distance_miles']} | "
                f"from_end_miles={route['distance_from_end_station_miles']} | "
                f"start_availability={route['start_station_availability']} | "
                f"end_availability={route['end_station_availability']}"
            )
            for idx, route in enumerate(candidate_routes, start=1)
        ]
    )


    prompt = f"""
You are helping recommend a Citi Bike ride.

Start point: {start_point}

End point: {end_point}

Here are pre-scored route candidates:

{formatted_candidates}

Return exactly the top {top_n} routes as a numbered list.

Each route must include:

- start station name
- end station name
- distance from user start point to start station
- bike route distance
- distance from end station to destination
- station availability

Keep the output concise and human-readable.
""".strip()


    try:

        response = client.responses.create(
            model="chatgpt-4o-latest",
            input=prompt
        )

        recommendation_text = response.output_text


    except Exception:

        recommendation_text = "AI recommendation unavailable. Using fallback ranking."


    return candidate_routes, recommendation_text


# ----------------- Test -----------------

if __name__ == "__main__":

    sample_start = (40.7195861164717, -74.0431174635887)
    sample_end = (40.7287448, -74.0321082)


    routes, text = generate_recommendation(
        sample_start,
        sample_end
    )


    print(text)


    print("\nReturned route objects:\n")

    for route in routes:
        print(route)