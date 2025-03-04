import requests
from datetime import datetime, timedelta
import folium
from folium.plugins import HeatMap
from flask import Flask, render_template_string
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from collections import Counter
import time
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import atexit

app = Flask(__name__)

# Global variables to store the map and zip code HTML
latest_map_html = ""
latest_zip_code_html = ""

@app.route('/')
def home():
    global latest_map_html, latest_zip_code_html

    # Render the map and zip code information as HTML
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hail Reports Map</title>
        <style>
            .top-right {{
                position: absolute;
                top: 10px;
                right: 10px;
                background-color: black;
                color: white;
                padding: 10px;
                border-radius: 5px;
                opacity: 0.8;
                z-index: 1000;
            }}
        </style>
    </head>
    <body>
        {latest_map_html}
        <div class="top-right">
            {latest_zip_code_html}
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template)

def reverse_geocode(geolocator, lat, lon, retries=2, backoff_factor=0.5):
    for attempt in range(retries):
        try:
            return geolocator.reverse(f"{lat},{lon}", timeout=10)
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding error: {e}. Retrying in {backoff_factor * (2 ** attempt)} seconds...")
            time.sleep(backoff_factor * (2 ** attempt))
    return None

def generate_map():
    global latest_map_html, latest_zip_code_html

    # Calculate the date range for the last week
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

    # Define the URL for the desired date range
    url = f"https://www.spc.noaa.gov/exper/reports/v3/src/getAllReports.php?combine&start={start_date}&end={end_date}&json"

    # Make the request
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()

        # Filter reports for hail ('HA') reports in Colorado ('CO')
        colorado_reports = [report for report in data if report.get('Type') == 'HA' and report.get('St') == 'CO']
        
        # Create a map centered on Colorado
        map_center = [39.0, -105.5]  # Coordinates to center the map
        colorado_map = folium.Map(location=map_center, zoom_start=7)

        # Prepare heat map data and collect zip codes
        heat_data = []
        zip_codes = []
        geolocator = Nominatim(user_agent="hail_map_app", timeout=10)  # Set timeout to 10 seconds
        for report in colorado_reports:
            lat = float(report.get('Lat')) / 100.0  # Convert to decimal degrees
            lon = float(report.get('Lon')) / -100.0  # Convert to decimal degrees
            heat_data.append([lat, lon])
            
            location = reverse_geocode(geolocator, lat, lon)
            if location and location.raw.get('address'):
                zipcode = location.raw['address'].get('postcode')
                if zipcode:
                    zip_codes.append(zipcode)
        
        # Add heat map layer
        HeatMap(heat_data).add_to(colorado_map)

        # Count zip codes and create HTML
        zip_code_counts = Counter(zip_codes)
        zip_code_html = "<h3>Hail Reports by Zip Code (Last 7 days)</h3>"
        zip_code_html += "<ul>"
        for zip_code, count in zip_code_counts.most_common():
            zip_code_html += f"<li>{zip_code}: {count} reports</li>"
        zip_code_html += "</ul>"

        latest_map_html = colorado_map._repr_html_()
        latest_zip_code_html = zip_code_html
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        latest_map_html = ""
        latest_zip_code_html = ""

# Schedule the update to run daily
scheduler = BackgroundScheduler(timezone=timezone('America/Denver'))
scheduler.add_job(func=generate_map, trigger='interval', days=1)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Initial map generation
generate_map()

if __name__ == '__main__':
    app.run()
