import pandas as pd
import requests
import time
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import base64
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
api_key = os.getenv("API_KEY")

@st.cache_data
def geocode_address_locationiq(address, api_key, retries=3):
    """Geocode an address using LocationIQ API."""
    url = f"https://us1.locationiq.com/v1/search.php?key={api_key}&q={address}&format=json"

    for attempt in range(retries):
        try:
            response = requests.get(url)
            data = response.json()

            if len(data) > 0:
                lat = data[0]['lat']
                lon = data[0]['lon']
                return float(lat), float(lon)
            else:
                print(f"Could not geocode address: {address}")
                return None, None
        except Exception as e:
            print(f"Error geocoding {address}: {e}")
            if attempt < retries - 1:
                print("Retrying...")
                time.sleep(2)  # Adding a delay before retry
            else:
                print("Max retries reached. Could not geocode address.")
                return None, None

def convert_google_drive_url(url):
    """Convert Google Drive URL to direct link."""
    if "drive.google.com" in url:
        file_id = url.split('/')[-2]
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    return url

def add_geocoded_columns_to_excel(excel_file, address_column, people_column, img_column, api_key):
    """Add geocoded columns to an Excel file."""
    xls = pd.ExcelFile(excel_file)
    all_data = []

    for sheet_name in xls.sheet_names:
        print(f"Processing sheet: {sheet_name}")
        data = pd.read_excel(xls, sheet_name=sheet_name)
        data = data[[address_column, people_column, img_column]]

        # Skip sheets without the necessary columns
        if address_column not in data.columns or people_column not in data.columns or img_column not in data.columns:
            print(f"Skipping sheet '{sheet_name}' - Missing required columns.")
            continue

        # Add Latitude and Longitude columns if they don't exist
        if "Latitude" not in data.columns:
            data["Latitude"] = None
        if "Longitude" not in data.columns:
            data["Longitude"] = None

        # Geocode each address and add latitude/longitude
        progress_bar = st.progress(0)
        for idx, address in enumerate(data[address_column]):
            if pd.notna(address) and not data.at[idx, "Latitude"]:
                lat, lon = geocode_address_locationiq(address, api_key)
                if lat is not None and lon is not None:
                    data.at[idx, "Latitude"] = lat
                    data.at[idx, "Longitude"] = lon
                    print(f"Geocoded '{address}': Latitude = {lat}, Longitude = {lon}")
            progress_bar.progress((idx + 1) / len(data))

        # Append the data from this sheet to the all_data list
        all_data.append(data)

    # Consolidate all sheets into one DataFrame
    consolidated_data = pd.concat(all_data, ignore_index=True)

    # Convert the 'Img' column to hyperlinks for Excel export
    def create_hyperlink_formula(url):
        return f'=HYPERLINK("{url}", "{url}")' if pd.notna(url) else None

    consolidated_data[img_column] = consolidated_data[img_column].apply(create_hyperlink_formula)

    return consolidated_data

def generate_map(data):
    """Generate a map from the given data."""
    # Create a map centered around the average latitude and longitude
    avg_lat = sum(entry["Latitude"] for entry in data) / len(data)
    avg_lon = sum(entry["Longitude"] for entry in data) / len(data)
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10, tiles='CartoDB dark_matter')

    # Add a banner to the top of the map
    banner_html = """
        <div style="position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    heigth: 150px;
                    background-color: #111;
                    color: white;
                    padding: 10px 20px;
                    font-family: Arial, sans-serif;
                    z-index: 9999;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;">
            <h1 style="margin: 0; font-size: 2rem;">Principles Exposure Map</h1>
            <div style="display: flex; gap: 20px;">
                <div style="text-align: center;">
                    <p style="margin: 0; font-size: 1.2rem;">3407</p>
                    <p style="margin: 0; font-size: 1.2rem;">people attended</p>
                </div>
                <div style="text-align: center;">
                    <p style="margin: 0; font-size: 1rem;">70</p>
                    <p style="margin: 0; font-size: 1rem;">location</p>
                </div>

            </div>
        </div>
    """
    m.get_root().html.add_child(folium.Element(banner_html))

    # Create a MarkerCluster with custom icons
    marker_cluster = MarkerCluster(
        icon_create_function="""
        function(cluster) {
            var markers = cluster.getAllChildMarkers();
            var totalPeople = 0;
            for (var i = 0; i < markers.length; i++) {
                var tooltipContent = markers[i].getTooltip().getContent();
                var peopleAttended = parseInt(tooltipContent.match(/(\d+) people Attended/)[1]);
                totalPeople += peopleAttended;
            }
            var c = ' marker-cluster-';
            if (totalPeople < 10) {
                c += 'small';
            } else if (totalPeople < 100) {
                c += 'medium';
            } else {
                c += 'large';
            }
            return new L.DivIcon({ html: '<div><span>' + totalPeople + '</span></div>', className: 'marker-cluster' + c, iconSize: new L.Point(40, 40) });
        }
        """
    ).add_to(m)

    # Define data with actual image URLs from Wikimedia Commons
    # Add markers for the filtered data
    circle_scaling_factor = 0.1  # Adjust this factor to scale the circle sizes appropriately

    for entry in data:
        # Calculate radius based on people served
        radius = int(entry["People Attended"]) * circle_scaling_factor

        # Convert Google Drive URL to direct link
        img_url = convert_google_drive_url(entry['Img'])
        print(f"Converted URL: {img_url}")  # Debugging: Print the converted URL

        # Tooltip content for hover
        tooltip_content = f"""
        <div style="width:150px; text-align:center;">
            <p>{entry['People Attended']} people Attended</p>
            <img src= {entry['Img']} width="150px">
        </div>
        """
        print(f"Tooltip content: {tooltip_content}")  # Debugging: Print the tooltip content

        # Popup content for click
        popup_html = f"""
        <html><body>
            <img src="{img_url}" width="150px">
        </body></html>
        """

        # Add the circle marker to the marker cluster
        marker = folium.CircleMarker(
            location=[entry["Latitude"], entry["Longitude"]],
            radius=radius,
            color="yellow",
            fill=True,
            fill_color="yellow",
            fill_opacity=0.7,
            tooltip=folium.Tooltip(tooltip_content, sticky=True),
            popup=folium.Popup(popup_html, max_width=300)
        )

        marker.add_to(marker_cluster)

    # Save the map as an HTML file
    map_html = 'Principles_Map.html'
    m.save(map_html)

    return m, map_html

def main():
    # Stylish title using HTML and CSS
    st.markdown("""
        <style>
        .title {
            font-size: 36px;
            font-weight: bold;
            color: orange;
            background-color: white;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="title">PJI Principles Map Viewer</div>
    """, unsafe_allow_html=True)

    # Upload dataset
    uploaded_file = st.file_uploader("Upload your dataset (Excel Format only, column names: Address, People Attended and Img):", type=["xlsx"])
    if uploaded_file:
        address_column = "Address"
        people_column = "People Attended"
        img_column = "Img"
        df = add_geocoded_columns_to_excel(uploaded_file, address_column, people_column, img_column, api_key)

        data = df.to_dict(orient="records")
        
        # Generate and display the map
        map_object, map_html = generate_map(data)
        folium_static(map_object, width=800, height=600)

        # Button to download the map as HTML
        with open(map_html, "rb") as f:
            html_bytes = f.read()
        st.download_button(
            label="Download Map as HTML",
            data=html_bytes,
            file_name="Principles_Map.html",
            mime="text/html"
        )

if __name__ == "__main__":
    main()
