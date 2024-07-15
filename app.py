from flask import Flask, render_template_string
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import folium
import pandas as pd
import time

app = Flask(__name__)
geolocator = Nominatim(user_agent="myGeocoder", timeout=10)  # Set timeout to 10 seconds

def reverse_geocode(lat, lon, retries=3, backoff_factor=0.3):
    for attempt in range(retries):
        try:
            return geolocator.reverse(f"{lat},{lon}")
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error: {e}. Retrying in {backoff_factor * (2 ** attempt)} seconds...")
            time.sleep(backoff_factor * (2 ** attempt))
    return None

def generate_map():
    # Sample data (should be replaced with actual data fetching logic)
    data = {
        'lat': [39.53, 39.45, 38.84],
        'lon': [-104.14, -103.97, -104.05],
        'damage': ['Severe', 'Moderate', 'Minor']
    }
    df = pd.DataFrame(data)

    # Create a map centered on Colorado
    colorado_map = folium.Map(location=[39.55, -104.95], zoom_start=6)

    # Initialize an empty list for zip code HTML
    zip_code_html = []

    # Add points to the map
    for idx, row in df.iterrows():
        lat, lon, damage = row['lat'], row['lon'], row['damage']
        location = reverse_geocode(lat, lon)

        if location:
            address = location.raw.get('address', {})
            zip_code = address.get('postcode', 'Unknown')
        else:
            zip_code = 'Unknown'

        folium.Marker(
            location=[lat, lon],
            popup=f"Damage: {damage}<br>ZIP Code: {zip_code}",
            icon=folium.Icon(color='red' if damage == 'Severe' else 'blue')
        ).add_to(colorado_map)

        zip_code_html.append(f"<p>Damage: {damage}, ZIP Code: {zip_code}</p>")

    # Return the map and the zip code HTML
    return colorado_map._repr_html_(), '\n'.join(zip_code_html)

@app.route('/')
def home():
    colorado_map, zip_code_html = generate_map()
    return render_template_string('''
        <html>
        <body>
            <h1>Hail Damage in Colorado</h1>
            {{ colorado_map|safe }}
            <div>
                {{ zip_code_html|safe }}
            </div>
        </body>
        </html>
    ''', colorado_map=colorado_map, zip_code_html=zip_code_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
