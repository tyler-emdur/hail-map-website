import requests
from datetime import datetime, timedelta
import folium
from folium.plugins import HeatMap
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    # Generate the map dynamically
    colorado_map = generate_map()
    
    # Render the map as HTML
    map_html = colorado_map._repr_html_()  # Get the HTML representation of the map
    return render_template_string(map_html)

def generate_map():
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
        map_center = [39.5501, -105.7821]  # Latitude and Longitude of Colorado's approximate center
        colorado_map = folium.Map(location=map_center, zoom_start=6)

        # Add points for reports
        for report in colorado_reports:
            lat = float(report.get('Lat')) / 100.0  # Convert to decimal degrees
            lon = float(report.get('Lon')) / -100.0  # Convert to decimal degrees
            hail_size = report.get('Size', 'Unknown')  # Get hail size, default to 'Unknown' if not present
            popup_text = f"Hail Size: {hail_size}\"<br>{report.get('Remark', 'No remark')}"

            folium.Marker(
                location=[lat, lon],
                popup=popup_text,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(colorado_map)

        # Convert points to list of lat-lon pairs for heat map
        heat_data = [[float(report.get('Lat')) / 100.0, float(report.get('Lon')) / -100.0] for report in colorado_reports]

        # Add heat map layer
        HeatMap(heat_data).add_to(colorado_map)

        return colorado_map
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
