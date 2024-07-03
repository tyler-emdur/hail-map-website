import os
import requests
import json
from datetime import datetime, timedelta
import folium
from folium.plugins import HeatMap
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory('static', 'colorado_reports_map_with_heat.html')

def generate_map():
    # Calculate the date range for the last week
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

    # Define the URL for the desired date range
    url = f"https://www.spc.noaa.gov/exper/reports/v3/src/getAllReports.php?combine&start={start_date}&end={end_date}&json"

    # Make the request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        # Filter reports for those in Colorado
        colorado_reports = [report for report in data if report.get('St') == 'CO']

        # Create a map centered on Colorado
        map_center = [39.5501, -105.7821]  # Latitude and Longitude of Colorado's approximate center
        colorado_map = folium.Map(location=map_center, zoom_start=6)

        # Add points for reports
        for report in colorado_reports:
            lat = float(report.get('Lat')) / 100.0  # Convert to decimal degrees
            lon = float(report.get('Lon')) / -100.0  # Convert to decimal degrees
            folium.Marker(
                location=[lat, lon],
                popup=f"{report.get('Type')}: {report.get('Remark')}",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(colorado_map)

        # Convert points to list of lat-lon pairs
        heat_data = [[float(report.get('Lat')) / 100.0, float(report.get('Lon')) / -100.0] for report in colorado_reports]

        # Add heat map layer
        HeatMap(heat_data).add_to(colorado_map)

        # Save the map to an HTML file in the static directory
        save_path = os.path.join('static', 'colorado_reports_map_with_heat.html')
        colorado_map.save(save_path)
        print(f"Map with heat map overlay has been created and saved to '{save_path}'")
    else:
        print(f"Failed to retrieve data: {response.status_code}")

if __name__ == "__main__":
    # Ensure the static directory exists
    os.makedirs('static', exist_ok=True)

    # Generate the map
    generate_map()

    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)
